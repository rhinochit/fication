"""Enroll one person across three poses: center, left, right — writes
directly to Supabase (supabase_client.py), no local database at all.

Each pose is captured and quality-gated separately (quality.py adjusts what
counts as "good" per pose — frontal for center, actually turned for left/right).
Each pose's embedding becomes its own face_data row in Supabase — there's no
per-pose column in that schema, but nothing requires one row per user either;
matching already compares against every stored sample and picks the best.

Re-running this for the same name reuses that person's existing user_id
(looked up by name in formal_profiles) and replaces their previous face_data
rows rather than accumulating duplicates.

Usage:
    python enroll.py "Rachit"
"""
import sys
import time

import cv2
import numpy as np

from embedding import detect_landmarks, make_landmarker
from identity import face_identity_encoding
from quality import assess
import supabase_client as sb_db

FRAMES_PER_POSE = 10
MIN_SAMPLE_INTERVAL = 0.2  # seconds between accepted samples

POSES = [
    ("center", "Look straight at the camera"),
    ("left", "Slowly turn your head to the LEFT"),
    ("right", "Slowly turn your head to the RIGHT"),
]


def capture_pose(cap, landmarker, pose, instruction):
    samples = []
    last_sample_time = 0.0

    print(f"{instruction} - capturing {FRAMES_PER_POSE} samples...")
    while len(samples) < FRAMES_PER_POSE:
        ok, frame = cap.read()
        if not ok:
            continue
        frame = cv2.flip(frame, 1)

        points = detect_landmarks(frame, landmarker, int(time.time() * 1000))
        if points is None:
            message, color, bbox = "No face", (0, 0, 220), None
        else:
            good, message, bbox = assess(frame, points, pose=pose)
            color = (0, 200, 0) if good else (0, 165, 255)

            now = time.time()
            if good and (now - last_sample_time) >= MIN_SAMPLE_INTERVAL:
                encoding = face_identity_encoding(frame)
                if encoding is not None:
                    samples.append(encoding)
                    last_sample_time = now

        if bbox is not None:
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)

        cv2.putText(frame, instruction, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(
            frame, f"{message} - {len(samples)}/{FRAMES_PER_POSE}",
            (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2,
        )
        cv2.imshow("Enroll - press q to cancel", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            return None

    return np.mean(samples, axis=0)


def enroll(name):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # DirectShow avoids MSMF's frame-buffering lag on Windows
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam.")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    landmarker = make_landmarker(num_faces=1)

    user_id = sb_db.get_or_create_user_by_name(name)
    sb_db.clear_face_data(user_id)  # re-enrolling replaces, doesn't accumulate
    consent_id = sb_db.create_consent(user_id, consent_type="face_enrollment", consent_method="local_capture")

    for pose, instruction in POSES:
        avg_embedding = capture_pose(cap, landmarker, pose, instruction)
        if avg_embedding is None:
            print("Enrollment cancelled.")
            cap.release()
            cv2.destroyAllWindows()
            return
        sb_db.save_face_data(user_id, avg_embedding, consent_id)
        print(f"Stored '{pose}' sample for '{name}' in Supabase.")

    cap.release()
    cv2.destroyAllWindows()
    print(f"Enrollment complete for '{name}' - center, left, and right poses stored in Supabase.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python enroll.py <name>")
        sys.exit(1)
    enroll(sys.argv[1])
