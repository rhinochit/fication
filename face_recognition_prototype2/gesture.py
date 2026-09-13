"""Hand gesture classification via MediaPipe HandLandmarker.

Same rule as the JS prototype (consent_driven_profile_viewer.html): a finger
is "up" if its tip sits above its PIP joint. Peace sign = index + middle up,
ring + pinky down. Open palm = all four up. Thumb ignored, same as the JS
version, for robustness.
"""
import os
import urllib.request

import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")

INDEX_TIP, INDEX_PIP = 8, 6
MIDDLE_TIP, MIDDLE_PIP = 12, 10
RING_TIP, RING_PIP = 16, 14
PINKY_TIP, PINKY_PIP = 20, 18


def ensure_model():
    if not os.path.exists(MODEL_PATH):
        print("Downloading hand landmark model (one-time, ~8MB)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    return MODEL_PATH


def make_hand_landmarker(num_hands=1, min_detection_confidence=0.3, min_presence_confidence=0.3,
                          min_tracking_confidence=0.3):
    """Same reasoning as embedding.make_landmarker — hands are smaller than
    faces in frame, so they're hit even harder by distance/lighting than
    faces are. Lowered from MediaPipe's 0.5 default for the same tradeoff.
    """
    base_options = mp_python.BaseOptions(model_asset_path=ensure_model())
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        # VIDEO mode tracks the hand between frames instead of re-running
        # full detection every time — same reasoning as embedding.py.
        running_mode=vision.RunningMode.VIDEO,
        num_hands=num_hands,
        min_hand_detection_confidence=min_detection_confidence,
        min_hand_presence_confidence=min_presence_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )
    return vision.HandLandmarker.create_from_options(options)


def _finger_up(landmarks, tip_idx, pip_idx):
    return landmarks[tip_idx].y < landmarks[pip_idx].y


def classify_gesture(bgr_frame, hand_landmarker, timestamp_ms):
    """Returns 'BUSINESS' (peace sign), 'INSTAGRAM' (open palm), or 'NONE'."""
    rgb = bgr_frame[:, :, ::-1]
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
    result = hand_landmarker.detect_for_video(mp_image, timestamp_ms)

    if not result.hand_landmarks:
        return "NONE"

    landmarks = result.hand_landmarks[0]
    index_up = _finger_up(landmarks, INDEX_TIP, INDEX_PIP)
    middle_up = _finger_up(landmarks, MIDDLE_TIP, MIDDLE_PIP)
    ring_up = _finger_up(landmarks, RING_TIP, RING_PIP)
    pinky_up = _finger_up(landmarks, PINKY_TIP, PINKY_PIP)

    if index_up and middle_up and not ring_up and not pinky_up:
        return "BUSINESS"
    if index_up and middle_up and ring_up and pinky_up:
        return "INSTAGRAM"
    return "NONE"
