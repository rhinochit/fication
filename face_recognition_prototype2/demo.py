"""Watches IMAGES_DIR (C:\\Users\\RACHIT\\Downloads\\test1\\saved_photos) for
new photos — dropped in by fication_backend's POST /identify endpoint, which
is how the phone app delivers a captured photo here — runs the identity +
gesture check on each one as it appears, and pushes the outcome to Supabase
(scan_logs) for the frontend to read.
camera app -> FastAPI -> saved_photos/ -> demo.py -> Supabase -> frontend.

The folder is expected to keep growing continuously, not be a fixed batch.
Only the most recently modified file is ever checked (see latest_image());
enrolled users are re-read from Supabase on every poll, so enrolling someone
new (via FastAPI's POST /enroll) while this is running takes effect without
a restart.

evaluate_photo() returns a plain dict describing what happened — no drawing,
no I/O — so the same result can be rendered (draw_result) and pushed to
Supabase without duplicating the decision logic. Which gesture reveals which
profile type is looked up per-user from gesture_mapping (falls back to the
peace-sign=formal / open-palm=informal default if that user hasn't set one).

The database push honors the same consent lock as the on-screen placard:
scan_logs is only ever written when status is 'revealed' (recognized AND a
gesture was read in the same photo) — a match alone never reaches Supabase
as an identity (scanned_user_id), same as it never reaches the screen as one.

No liveness/blink detection here — a single still photo has no time
dimension for that check to run on.

Usage:
    python demo.py
    (Ctrl+C or q in the result window to stop)
"""
import os
import threading
import time

import cv2

from embedding import detect_landmarks, make_landmarker, normalize_lighting
import identity
from identity import face_identity_encoding, best_match, MATCH_DISTANCE_THRESHOLD
from gesture import classify_gesture, make_hand_landmarker
from quality import face_bbox
import supabase_client as sb_db

IMAGES_DIR = r"C:\Users\RACHIT\Downloads\test1\saved_photos"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "images_output")
POLL_INTERVAL = 1.0  # seconds between checking the folder for new images
CACHE_REFRESH_INTERVAL = 5.0  # seconds between re-fetching enrolled users / gesture mappings
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")

BUSINESS_COLOR = (170, 90, 40)    # BGR, indigo-ish — matches the business-card overlay
INSTAGRAM_COLOR = (110, 40, 200)  # BGR, magenta-ish — matches the Instagram overlay
PENDING_COLOR = (0, 200, 200)     # amber — recognized, but no gesture read
UNKNOWN_COLOR = (0, 0, 220)


def draw_placard(frame, bbox, lines, color):
    """Draws a filled placard anchored just below the given face bbox."""
    h, w = frame.shape[:2]
    x0, _, x1, y1 = bbox
    cx = (x0 + x1) // 2

    font = cv2.FONT_HERSHEY_SIMPLEX
    sizes = [cv2.getTextSize(line, font, scale, 2)[0] for line, scale in lines]
    box_w = max(size[0] for size in sizes) + 24
    box_h = sum(size[1] for size in sizes) + 12 * (len(lines) + 1)

    px0 = max(0, min(w - box_w, cx - box_w // 2))
    py0 = min(h - box_h, y1 + 10)
    px1, py1 = px0 + box_w, py0 + box_h

    overlay = frame.copy()
    cv2.rectangle(overlay, (px0, py0), (px1, py1), color, -1)
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
    cv2.rectangle(frame, (px0, py0), (px1, py1), color, 2)

    ty = py0 + 12
    for (line, scale), size in zip(lines, sizes):
        ty += size[1]
        tx = px0 + (box_w - size[0]) // 2
        cv2.putText(frame, line, (tx, ty), font, scale, (255, 255, 255), 2, cv2.LINE_AA)
        ty += 12


def evaluate_photo(frame, face_landmarker, hand_landmarker, users, gesture_map=None):
    """Runs the identity + gesture check on one photo. Returns a plain dict —
    status, bbox, user_id, name, mode, distance — with no drawing or I/O.

    gesture_map: optional {(user_id, gesture_type): target_type} from
    supabase_client.load_all_gesture_mappings() — pass a cached copy to
    avoid a live Supabase call per photo; omit to fall back to a live
    get_gesture_target() lookup (what callers that don't cache still get).

    Lighting normalization runs once here, on a copy used only for
    detection/encoding — bbox math still applies to the original frame
    (same dimensions either way), and draw_result draws on the original,
    unaltered frame.
    """
    detect_frame = normalize_lighting(frame)

    timestamp_ms = int(time.time() * 1000)
    points = detect_landmarks(detect_frame, face_landmarker, timestamp_ms)
    if points is None:
        return {"status": "no_face", "bbox": None, "user_id": None,
                "name": None, "mode": None, "distance": float("inf")}

    bbox = face_bbox(frame.shape, points)
    encoding_512 = face_identity_encoding(detect_frame)
    # Stored samples from Supabase are already reduced to 128-d (see
    # supabase_client.save_face_data) — the live encoding must go through
    # the identical fixed projection or distances are meaningless.
    encoding = sb_db.reduce_to_128(encoding_512) if encoding_512 is not None else None
    name, distance = best_match(encoding, users) if encoding is not None else (None, float("inf"))
    recognized = distance <= MATCH_DISTANCE_THRESHOLD

    if not recognized:
        return {"status": "unrecognized", "bbox": bbox, "user_id": None,
                "name": None, "mode": None, "distance": distance}

    user_id = next((uid for uid, n, _pose, _emb in users if n == name), None)
    gesture = classify_gesture(detect_frame, hand_landmarker, timestamp_ms)

    if gesture == "NONE":
        # Matched internally, but nothing is revealed without a gesture.
        return {"status": "awaiting_gesture", "bbox": bbox, "user_id": user_id,
                "name": None, "mode": None, "distance": distance, "gesture": gesture}

    default_mode = sb_db.DEFAULT_TARGET.get(gesture)
    if gesture_map is not None:
        gesture_type = sb_db.GESTURE_TYPE.get(gesture)
        mode = gesture_map.get((user_id, gesture_type), default_mode)
    else:
        mode = sb_db.get_gesture_target(user_id, gesture, default=default_mode)
    return {"status": "revealed", "bbox": bbox, "user_id": user_id,
            "name": name, "mode": mode, "distance": distance, "gesture": gesture}


def draw_result(frame, result):
    """Renders an evaluate_photo() result onto a copy of the frame."""
    out = frame.copy()
    status, bbox = result["status"], result["bbox"]

    if status == "no_face":
        cv2.putText(out, "No face detected", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, UNKNOWN_COLOR, 2)
        return out

    cv2.rectangle(out, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 255, 255), 1)

    if status == "unrecognized":
        draw_placard(out, bbox, [(f"Unrecognized (dist {result['distance']:.2f})", 0.6)], UNKNOWN_COLOR)
    elif status == "awaiting_gesture":
        draw_placard(out, bbox, [("No gesture read", 0.55)], PENDING_COLOR)
    elif result["mode"] == "formal_profile":
        draw_placard(out, bbox, [(result["name"], 0.75), ("Business Card", 0.55)], BUSINESS_COLOR)
    else:
        draw_placard(out, bbox, [(result["name"], 0.75), ("Instagram", 0.55)], INSTAGRAM_COLOR)

    return out


def list_images():
    if not os.path.isdir(IMAGES_DIR):
        return []
    return [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(IMAGE_EXTENSIONS)]


def latest_image():
    """Returns (filename, mtime) of the most recently modified image in
    IMAGES_DIR, or (None, None) if there isn't one. Modification time, not
    filename, decides "most recent" — this also means a file that gets
    overwritten in place (same name, new content) counts as new again,
    since its mtime changes.
    """
    files = list_images()
    if not files:
        return None, None
    return max(
        ((f, os.path.getmtime(os.path.join(IMAGES_DIR, f))) for f in files),
        key=lambda pair: pair[1],
    )


def main():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    face_landmarker = make_landmarker(num_faces=1)
    hand_landmarker = make_hand_landmarker(num_hands=1)

    print("Preloading CLIP model + its face detector...")
    identity.preload()  # otherwise the first photo processed eats the model-load stall
    print("Models loaded.")

    last_signature = None  # (filename, mtime) of whatever was last checked
    print(f"Watching {IMAGES_DIR} for the most recent photo... (Ctrl+C or q to stop)")

    # Enrolled users + gesture mappings were previously re-fetched from Supabase
    # on every single photo — 2-4 sequential network round-trips stacking up
    # on the hot path, which is most of what "working really slowly" was.
    # Cached here and refreshed periodically instead; a new enrollment now
    # takes up to CACHE_REFRESH_INTERVAL seconds to be picked up, rather than
    # being instant — a fine trade since enrollment happens ahead of a demo,
    # not mid-scan.
    users_cache = []
    gesture_map_cache = {}
    last_cache_refresh = 0.0

    try:
        while True:
            filename, mtime = latest_image()
            signature = (filename, mtime)

            if filename is not None and signature != last_signature:
                path = os.path.join(IMAGES_DIR, filename)
                frame = cv2.imread(path)

                if frame is None:
                    pass  # might still be mid-write — retry next poll, don't update last_signature
                else:
                    now = time.time()
                    if now - last_cache_refresh >= CACHE_REFRESH_INTERVAL:
                        users_cache = sb_db.load_all_face_data()
                        gesture_map_cache = sb_db.load_all_gesture_mappings()
                        last_cache_refresh = now

                    if not users_cache:
                        print(f"{filename}: no enrolled users yet - enroll someone via POST /enroll first")
                    else:
                        result = evaluate_photo(frame, face_landmarker, hand_landmarker,
                                                 users_cache, gesture_map_cache)

                        if result["status"] == "revealed":
                            # Consent lock applies to the database too: a match alone never
                            # reaches Supabase as an identity, only a match + gesture does.
                            # Fired on a background thread — nothing downstream needs its
                            # result, so there's no reason to block the loop on this write.
                            threading.Thread(
                                target=sb_db.save_scan_log,
                                args=(result["user_id"], result["gesture"], result["distance"]),
                                daemon=True,
                            ).start()

                        annotated = draw_result(frame, result)
                        out_path = os.path.join(OUTPUT_DIR, filename)
                        cv2.imwrite(out_path, annotated)
                        print(f"{filename}: {result['status']} -> {out_path}")

                        cv2.imshow("Fication - watching images/ (q to quit)", annotated)

                    last_signature = signature

            key = cv2.waitKey(int(POLL_INTERVAL * 1000)) & 0xFF
            if key == ord("q"):
                break
    except KeyboardInterrupt:
        pass

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
