"""Lightweight liveness signal: blink detection via eye-aspect-ratio (EAR) over time.

Not real anti-spoof security — a good photo held steady with the right crop
could still pass. It's a prototype-level check that a printed photo or a
phone screen held up won't show a normal blink pattern, which is enough to
demo the concept and to harden later with a proper model if it matters.

Operates on embedding.py's *normalized* landmark output reshaped back to
points — EAR is a ratio of distances, so it's unaffected by the uniform
recenter/rescale embedding.py already applied. No second detection pass needed.
"""
import time
from collections import deque

import numpy as np

# 6-point eye contours (2 lid pairs + 2 corners), standard MediaPipe face mesh indices.
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
LEFT_EYE = [362, 385, 387, 263, 373, 380]

EAR_BLINK_THRESHOLD = 0.21
BLINK_WINDOW_SECONDS = 4.0


def _ear(points):
    p1, p2, p3, p4, p5, p6 = points
    vertical = np.linalg.norm(p2 - p6) + np.linalg.norm(p3 - p5)
    horizontal = np.linalg.norm(p1 - p4)
    if horizontal < 1e-6:
        return 0.4
    return vertical / (2.0 * horizontal)


def eye_aspect_ratio(points_xy):
    """points_xy: Nx2 (or Nx3, extra columns ignored) array of landmark points."""
    right = _ear(points_xy[RIGHT_EYE][:, :2])
    left = _ear(points_xy[LEFT_EYE][:, :2])
    return (right + left) / 2.0


class LivenessTracker:
    def __init__(self):
        self._events = deque()  # (timestamp, blinked)
        self._was_closed = False

    def reset(self):
        self._events.clear()
        self._was_closed = False

    def update(self, embedding):
        points = embedding.reshape(-1, 3)
        ear = eye_aspect_ratio(points)
        is_closed = ear < EAR_BLINK_THRESHOLD

        blinked = self._was_closed and not is_closed
        self._was_closed = is_closed

        now = time.time()
        self._events.append((now, blinked))
        cutoff = now - BLINK_WINDOW_SECONDS
        while self._events and self._events[0][0] < cutoff:
            self._events.popleft()

    def is_live(self):
        if not self._events:
            return False
        observed_span = self._events[-1][0] - self._events[0][0]
        if observed_span < BLINK_WINDOW_SECONDS * 0.75:
            return False  # not enough observation time yet to trust an absence of blinks
        return any(blinked for _, blinked in self._events)
