"""Frame quality gates for enrollment.

Rejects frames before they get averaged into the stored embedding, instead
of trusting whatever the camera happened to see. Checks framing (too close /
too far), head pose (turned away from camera), lighting, and blur.
"""
import cv2
import numpy as np

MIN_FACE_WIDTH_RATIO = 0.18  # face must span at least this fraction of frame width
MAX_FACE_WIDTH_RATIO = 0.65  # ...and no more than this
CENTER_MAX_YAW = 0.35        # 'center' pose: reject anything turned past this
TURN_MIN_YAW = 0.30          # 'left'/'right' pose: reject anything not turned at least this much
TURN_MAX_YAW = 0.85          # ...or turned so far the landmarker's own tracking gets unreliable
MIN_BRIGHTNESS = 60
MAX_BRIGHTNESS = 200
MIN_SHARPNESS = 60.0         # Laplacian variance — lower reads as motion blur / out of focus

LEFT_EYE_OUTER = 33
RIGHT_EYE_OUTER = 263
NOSE_TIP = 1


def face_bbox(frame_shape, points):
    """points: raw Nx3 array from embedding.detect_landmarks (normalized image coords).
    Returns (x0, y0, x1, y1) in pixels.
    """
    h, w = frame_shape[:2]
    pixel_xy = points[:, :2] * np.array([w, h], dtype=np.float32)
    xs, ys = pixel_xy[:, 0], pixel_xy[:, 1]
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def assess(frame, points, pose="center"):
    """points: the raw Nx3 array from embedding.detect_landmarks (normalized image coords).
    pose: 'center', 'left', or 'right' — which capture stage this frame is for.
    Returns (ok: bool, message: str, bbox: (x0, y0, x1, y1) in pixels).
    """
    h, w = frame.shape[:2]
    pixel_xy = points[:, :2] * np.array([w, h], dtype=np.float32)

    bbox = face_bbox(frame.shape, points)
    xs = pixel_xy[:, 0]
    width_ratio = (xs.max() - xs.min()) / w

    if width_ratio < MIN_FACE_WIDTH_RATIO:
        return False, "Move closer", bbox
    if width_ratio > MAX_FACE_WIDTH_RATIO:
        return False, "Move back", bbox

    nose = pixel_xy[NOSE_TIP]
    left_dist = np.linalg.norm(pixel_xy[LEFT_EYE_OUTER] - nose)
    right_dist = np.linalg.norm(pixel_xy[RIGHT_EYE_OUTER] - nose)
    asymmetry = abs(left_dist - right_dist) / max(left_dist, right_dist, 1e-6)

    if pose == "center":
        if asymmetry > CENTER_MAX_YAW:
            return False, "Face the camera", bbox
    else:
        if asymmetry < TURN_MIN_YAW:
            return False, f"Turn your head further to the {pose}", bbox
        if asymmetry > TURN_MAX_YAW:
            return False, "That's too far, turn back a little", bbox

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = gray.mean()
    if brightness < MIN_BRIGHTNESS:
        return False, "Too dark", bbox
    if brightness > MAX_BRIGHTNESS:
        return False, "Too bright", bbox

    if cv2.Laplacian(gray, cv2.CV_64F).var() < MIN_SHARPNESS:
        return False, "Hold still", bbox

    return True, "Good", bbox
