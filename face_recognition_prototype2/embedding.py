"""Face embedding via MediaPipe FaceLandmarker — no dlib, no training, Windows-friendly.

The landmark mesh itself isn't an identity embedding, so this normalizes it:
recentered on the nose bridge and scaled by inter-ocular distance, which
cancels out camera distance and head position, leaving a vector that mostly
reflects face shape. Good enough for a small enrolled set; not a substitute
for a trained recognition model if the demo needs to scale past a room.
"""
import os
import urllib.request

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "face_landmarker.task")

LEFT_EYE_OUTER = 33
RIGHT_EYE_OUTER = 263
NOSE_BRIDGE = 168


def ensure_model():
    if not os.path.exists(MODEL_PATH):
        print("Downloading face landmark model (one-time, ~4MB)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    return MODEL_PATH


def make_landmarker(num_faces=1, min_detection_confidence=0.3, min_presence_confidence=0.3,
                     min_tracking_confidence=0.3):
    """Confidence thresholds default to 0.3, below MediaPipe's own 0.5 default —
    that default is tuned conservatively for close, well-lit, front-facing
    faces. Lowering it trades some false-positive risk for actually detecting
    smaller (farther-away) or poorly-lit faces at all, which is the point.
    """
    base_options = mp_python.BaseOptions(model_asset_path=ensure_model())
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        # VIDEO mode tracks the face between frames instead of re-running full
        # detection on every one — much cheaper for a continuous webcam loop.
        # Requires timestamps that strictly increase across calls on this
        # same landmarker instance.
        running_mode=vision.RunningMode.VIDEO,
        num_faces=num_faces,
        min_face_detection_confidence=min_detection_confidence,
        min_face_presence_confidence=min_presence_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )
    return vision.FaceLandmarker.create_from_options(options)


def normalize_lighting(bgr_frame):
    """CLAHE (contrast-limited adaptive histogram equalization) on the L
    channel in LAB space — evens out dim, overexposed, or backlit shots
    before detection/encoding ever sees them. Cheap (a few ms) and doesn't
    distort color the way naive global contrast stretching would.
    """
    lab = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_eq = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((l_eq, a, b)), cv2.COLOR_LAB2BGR)


def detect_landmarks(bgr_frame, landmarker, timestamp_ms):
    """Returns the raw Nx3 landmark array (image-normalized x, y, and relative z), or None."""
    rgb = bgr_frame[:, :, ::-1]
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
    result = landmarker.detect_for_video(mp_image, timestamp_ms)

    if not result.face_landmarks:
        return None

    return np.array([[p.x, p.y, p.z] for p in result.face_landmarks[0]], dtype=np.float32)


def normalize(points):
    """Recenters on the nose bridge and rescales by inter-ocular distance, then flattens."""
    pts = points.copy()
    pts -= pts[NOSE_BRIDGE]
    ocular_dist = np.linalg.norm(pts[LEFT_EYE_OUTER] - pts[RIGHT_EYE_OUTER])
    if ocular_dist < 1e-6:
        return None
    pts /= ocular_dist
    return pts.flatten()


def extract_embedding(bgr_frame, landmarker, timestamp_ms):
    """Returns a normalized 1D landmark embedding for the largest face, or None."""
    points = detect_landmarks(bgr_frame, landmarker, timestamp_ms)
    if points is None:
        return None
    return normalize(points)


def cosine_similarity(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
