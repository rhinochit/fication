"""Live recognition: matches each webcam frame's face against everyone
enrolled in Supabase.

The CLIP encoder (identity.py) is the expensive step, so it runs on a
background thread (IdentityWorker) so it never blocks the render loop; the
video renders every frame at full camera speed regardless, with the last
known label held on screen in between checks.

Usage:
    python recognize.py
"""
import cv2

from identity import IdentityWorker, MATCH_DISTANCE_THRESHOLD
import supabase_client as sb_db

CHECK_INTERVAL = 0.5  # seconds between identity checks


def main():
    users = sb_db.load_all_face_data()
    if not users:
        print("No enrolled users yet - run enroll.py first.")
        return

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # DirectShow avoids MSMF's frame-buffering lag on Windows
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    identity_worker = IdentityWorker(users, CHECK_INTERVAL, encode_fn=sb_db.reduce_to_128)

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)  # mirror, so it behaves like a normal webcam view

        identity_worker.submit_frame(frame)  # never blocks — background thread picks it up
        name, distance = identity_worker.get_result()
        recognized = distance <= MATCH_DISTANCE_THRESHOLD

        if name is None:
            label, color = "No face / checking...", (0, 165, 255)
        elif recognized:
            label, color = f"{name} (dist {distance:.2f})", (0, 200, 0)
        else:
            label, color = f"Unknown (dist {distance:.2f})", (0, 0, 220)

        cv2.putText(frame, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        cv2.imshow("Recognize - press q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    identity_worker.stop()


if __name__ == "__main__":
    main()
