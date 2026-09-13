"""Face identity matching via a Hugging Face CLIP image embedding (transformers).

Same public interface as the dlib version this clone started from —
face_identity_encoding, best_match, IdentityWorker, MATCH_DISTANCE_THRESHOLD —
so enroll.py / recognize.py / demo.py needed zero changes. Only this file's
internals differ.

Face detection/cropping reuses MediaPipe FaceLandmarker (embedding.py)
instead of dlib, so this variant needs no dlib / Build Tools install at all —
just mediapipe + transformers + torch.

Honest framing: CLIP is a general-purpose image embedding model, trained for
image/text similarity, not specifically for telling different people's faces
apart the way dlib's ResNet-34 is. This clone exists to actually measure that
gap, not to assume CLIP wins on accuracy — see MATCH_DISTANCE_THRESHOLD.
"""
import threading
import time

import numpy as np
import torch
from transformers import CLIPModel, CLIPProcessor

from embedding import make_landmarker, detect_landmarks
from quality import face_bbox

MODEL_NAME = "openai/clip-vit-base-patch32"

# Euclidean distance on L2-normalized embeddings is monotonic with cosine
# similarity (dist^2 = 2 - 2*cos_sim), so this keeps the same "lower is
# better" semantics as the dlib version's threshold. Unlike dlib's 0.6 (a
# tested library default), this is a starting guess — CLIP wasn't trained
# for face verification, so this needs real tuning against enrolled faces.
MATCH_DISTANCE_THRESHOLD = 0.9

_model = None
_processor = None
_landmarker = None
_landmarker_ts = 1000


def _load_model():
    global _model, _processor
    if _model is None:
        print("Loading CLIP model (one-time download, ~600MB on first run)...")
        _model = CLIPModel.from_pretrained(MODEL_NAME)
        _processor = CLIPProcessor.from_pretrained(MODEL_NAME)
        _model.eval()
    return _model, _processor


def preload():
    """Forces the CLIP model and its face detector to load right now,
    instead of lazily on first use. Call this once at process startup
    (FastAPI's lifespan, or the top of demo.py's main()) so the first real
    photo doesn't pay model-loading latency — this doesn't make any single
    CLIP call faster, it just moves the one-time load cost earlier.
    """
    _load_model()
    _detector()


def _detector():
    global _landmarker
    if _landmarker is None:
        _landmarker = make_landmarker(num_faces=1)
    return _landmarker


def _crop_face(bgr_frame):
    """Finds the face via MediaPipe and returns a padded RGB crop, or None."""
    global _landmarker_ts
    _landmarker_ts += 33
    points = detect_landmarks(bgr_frame, _detector(), _landmarker_ts)
    if points is None:
        return None

    x0, y0, x1, y1 = face_bbox(bgr_frame.shape, points)
    h, w = bgr_frame.shape[:2]
    pad_x, pad_y = int((x1 - x0) * 0.15), int((y1 - y0) * 0.15)
    x0, y0 = max(0, x0 - pad_x), max(0, y0 - pad_y)
    x1, y1 = min(w, x1 + pad_x), min(h, y1 + pad_y)
    if x1 <= x0 or y1 <= y0:
        return None

    return bgr_frame[y0:y1, x0:x1][:, :, ::-1]  # BGR crop -> RGB


def face_identity_encoding(bgr_frame):
    """Returns an L2-normalized CLIP image embedding for the detected face, or None."""
    rgb_crop = _crop_face(bgr_frame)
    if rgb_crop is None:
        return None

    model, processor = _load_model()
    inputs = processor(images=rgb_crop, return_tensors="pt")
    with torch.no_grad():
        # get_image_features returns a structured BaseModelOutputWithPooling
        # in this transformers version, not a plain tensor — pooler_output is
        # the actual 512-d pooled/projected embedding; last_hidden_state (the
        # raw 50-token patch sequence) is NOT what we want to compare on.
        features = model.get_image_features(**inputs)

    embedding = features.pooler_output[0].numpy().astype(np.float32)
    norm = np.linalg.norm(embedding)
    if norm < 1e-6:
        return None
    return embedding / norm


def best_match(live_encoding, samples):
    """samples: [(user_id, name, pose, encoding), ...].
    Returns (name, distance) — LOWER distance is a better match. No samples
    at all returns (None, inf).
    """
    if not samples:
        return None, float("inf")

    scored = []
    for _, name, _pose, stored in samples:
        stored = np.asarray(stored, dtype=np.float32).flatten()
        if stored.shape[0] != live_encoding.shape[0]:
            print(f"⚠ Shape mismatch for {name}: {stored.shape} vs {live_encoding.shape}, skipping")
            continue
        distance = float(np.linalg.norm(live_encoding - stored))
        scored.append((name, distance))

    if not scored:
        return None, float("inf")
    scored.sort(key=lambda pair: pair[1])
    return scored[0]


class IdentityWorker:
    """Runs identity checks on a background thread so the video render loop
    never blocks on them — same design as the dlib version, since a heavy
    model call (CLIP's ViT forward pass here) should never stall rendering.

    encode_fn: optional transform applied to the raw 512-d embedding before
    matching — pass supabase_client.reduce_to_128 when `users` came from
    Supabase, since those stored samples are already reduced to 128-d and a
    raw 512-d live embedding won't compare against them (shape mismatch).
    Defaults to a no-op for matching against un-reduced samples.
    """

    def __init__(self, users, check_interval, encode_fn=None):
        self.users = users
        self.check_interval = check_interval
        self.encode_fn = encode_fn or (lambda embedding: embedding)
        self._lock = threading.Lock()
        self._latest_frame = None
        self._name, self._distance = None, float("inf")
        self._stop = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def submit_frame(self, frame):
        with self._lock:
            self._latest_frame = frame.copy()

    def get_result(self):
        with self._lock:
            return self._name, self._distance

    def stop(self):
        self._stop = True
        self._thread.join(timeout=1)

    def _run(self):
        while not self._stop:
            with self._lock:
                frame = self._latest_frame
                self._latest_frame = None

            if frame is not None:
                encoding = face_identity_encoding(frame)
                if encoding is not None:
                    name, distance = best_match(self.encode_fn(encoding), self.users)
                else:
                    name, distance = None, float("inf")
                with self._lock:
                    self._name, self._distance = name, distance

            time.sleep(self.check_interval)
