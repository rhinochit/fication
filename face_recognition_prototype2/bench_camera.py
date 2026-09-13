"""Isolates the camera+display pipeline from all CV processing — prints
real FPS every second. Run this alone: if it's already choppy or reports a
low FPS number, the bottleneck is the webcam/driver/display, not our code.

Usage:
    python bench_camera.py
"""
import time

import cv2

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

frame_count = 0
window_start = time.time()
fps = 0.0

while True:
    ok, frame = cap.read()
    if not ok:
        break
    frame = cv2.flip(frame, 1)

    frame_count += 1
    now = time.time()
    if now - window_start >= 1.0:
        fps = frame_count / (now - window_start)
        frame_count = 0
        window_start = now
        print(f"FPS: {fps:.1f}")

    cv2.putText(frame, f"FPS: {fps:.1f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    cv2.imshow("Camera-only benchmark - press q to quit", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
