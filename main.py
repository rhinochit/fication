import base64
import os
import sys
from contextlib import asynccontextmanager

import cv2
import numpy as np
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Reuses the CV pipeline from face_recognition_prototype2 directly — no
# separate `demo.py` process to remember to start, and no up-to-1-second
# polling delay. evaluate_photo() runs the moment a photo is saved.
PROTOTYPE_DIR = r"C:\Users\RACHIT\Desktop\PROJECTS\LearnClaude\face_recognition_prototype2"
sys.path.insert(0, PROTOTYPE_DIR)

import identity  # noqa: E402
from embedding import make_landmarker  # noqa: E402
from gesture import make_hand_landmarker  # noqa: E402
from demo import evaluate_photo, draw_result  # noqa: E402
import supabase_client as sb_db  # noqa: E402

_face_landmarker = None
_hand_landmarker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _face_landmarker, _hand_landmarker
    print("Preloading CLIP model + MediaPipe detectors...")
    identity.preload()
    _face_landmarker = make_landmarker(num_faces=1)
    _hand_landmarker = make_hand_landmarker(num_hands=1)
    print("Models loaded — ready to process captures.")
    yield


app = FastAPI(lifespan=lifespan)

# Mount the static directory so CSS/JS/Images load correctly
app.mount("/static/", StaticFiles(directory="static"), name="static")

# Ensure a directory exists to store captured photos
os.makedirs("saved_photos", exist_ok=True)

# JSON Data representing your connections log
CONNECTIONS_DATABASE = [
    {
        "id": "0928",
        "type": "formal",
        "type_label": "FORMAL PROFILE",
        "time": "JUST NOW",
        "name": "ELENA ROSTOVA",
        "title": "VP OF PRODUCT ENGINEERING",
        "company": "VEKTOR LABS",
        "email": "elena@vektor.io",
        "phone": "+1 (415) 890-2134",
        "avatar": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=faces",
        "info_boxes": {
            "working_on": "Currently architecting distributed spatial computing & tactile neural vision networks at Vektor Labs. Launching v2.4 this Q3 with real-time hand-tracking synchronization.",
            "stack": "Specialized in systems engineering with Rust and C++, high-throughput neural pipelines using Python and PyTorch, alongside reactive frontend interfaces built in TypeScript, React, WebGPU, and CUDA.",
            "proud_of": "Building the sub-10ms neural tactile processing engine from scratch, enabling seamless zero-calibration spatial interaction across heterogeneous hardware.",
            "philosophy": "Ruthless simplification over premature abstraction. Direct, low-latency communication loops both in silicon architecture and engineering teams."
        }
    }
]

# 2. Separate Social Cards Database
SOCIAL_DATABASE = [
    {
        "id": "S-0929",
        "type": "social",
        "name": "ELENA ROSTOVA",
        "location": "SAN FRANCISCO, CA",
        "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&h=600&fit=crop&crop=faces",
        "strength": "Finding hidden underground electronic sets, making matcha that actually tastes good, and debugging complex distributed systems with a grin.",
        "dating_me": "Spontaneous weekend road trips down Highway 1, debating sci-fi world-building, and having an intensely competitive Mario Kart rival.",
        "life_goal": "Build an open-source tactile spatial computer while spending at least one month each year disconnected in Patagonia.",
        "heart": "Fresh sourdough, witty banter, and someone who gets genuinely excited explaining their niche obsessive hobbies."
    }
]

def _get_formal_card(user_id):
    sb = sb_db.get_client()
    rows = sb.table("formal_profiles").select("*").eq("user_id", user_id).execute().data
    if not rows:
        return None
    profile = rows[0]
    prompts = (
        sb.table("profile_prompts")
        .select("prompt_label, response_text")
        .eq("user_id", user_id)
        .eq("profile_type", "formal")
        .execute()
        .data
    )
    return {
        "id": profile["user_id"],
        "name": profile.get("name"),
        "title": profile.get("title"),
        "company": profile.get("company"),
        "email": profile.get("email"),
        "phone": profile.get("phone"),
        "avatar": profile.get("photo_url"),
        "info_boxes": {p["prompt_label"]: p["response_text"] for p in prompts},
    }


def _get_social_card(user_id):
    sb = sb_db.get_client()
    rows = sb.table("informal_profiles").select("*").eq("user_id", user_id).execute().data
    if not rows:
        return None
    profile = rows[0]
    prompts = (
        sb.table("profile_prompts")
        .select("prompt_label, response_text")
        .eq("user_id", user_id)
        .eq("profile_type", "informal")
        .execute()
        .data
    )
    prompt_map = {p["prompt_label"]: p["response_text"] for p in prompts}
    return {
        "id": profile["user_id"],
        "name": profile.get("name"),
        "location": profile.get("location"),
        "avatar": profile.get("photo_url"),
        "strength": prompt_map.get("strength"),
        "dating_me": prompt_map.get("dating_me"),
        "life_goal": prompt_map.get("life_goal"),
        "heart": prompt_map.get("heart"),
    }


@app.get("/api/connections")
def get_connections(user_id: str = None):
    """user_id present -> the real scanned person's card from Supabase.
    Omitted -> the placeholder demo data, unchanged, for viewing the page
    without having scanned anyone yet.
    """
    if user_id:
        card = _get_formal_card(user_id)
        return card if card else {"error": "No formal profile found for this user"}
    return CONNECTIONS_DATABASE

@app.get("/api/social-connections")
def get_social_connections(user_id: str = None):
    if user_id:
        card = _get_social_card(user_id)
        return card if card else {"error": "No informal profile found for this user"}
    return SOCIAL_DATABASE

def _json_safe(result):
    """evaluate_photo() uses float('inf') for 'no match' — not valid JSON,
    would break the frontend's JSON.parse. None reads the same either way.
    """
    safe = dict(result)
    if safe.get("distance") == float("inf"):
        safe["distance"] = None
    return safe

@app.post("/api/save-photo")
async def save_photo(request: Request):
    data = await request.json()
    image_data = data.get("image")

    if not image_data:
        return {"status": "error", "message": "No image data found"}

    # Strip the base64 header (e.g., 'data:image/png;base64,')
    encoded_data = image_data.split(",")[1]
    decoded_image = base64.b64decode(encoded_data)

    # Define file path to save inside saved_photos directory
    file_path = "saved_photos/capture.png"

    with open(file_path, "wb") as fh:
        fh.write(decoded_image)

    # Process this exact capture right now — decode straight from the bytes
    # already in memory rather than re-reading the file we just wrote.
    frame = cv2.imdecode(np.frombuffer(decoded_image, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        return {"status": "error", "message": "Photo saved, but could not decode it for processing"}

    users = sb_db.load_all_face_data()
    if not users:
        return {"status": "success", "message": "Photo saved, but no enrolled users yet", "scan": None}

    result = evaluate_photo(frame, _face_landmarker, _hand_landmarker, users)

    if result["status"] == "revealed":
        # Same consent lock as everywhere else: only a match + gesture together
        # ever reaches Supabase as an identity.
        sb_db.save_scan_log(result["user_id"], result["gesture"], result["distance"])

    # The same placard demo.py draws in its own desktop window — but that
    # window only exists on this machine. Sending the annotated image back
    # in the response is what actually makes it visible wherever the photo
    # was taken (the phone/browser), instead of a window nobody's looking at.
    annotated = draw_result(frame, result)
    ok, buf = cv2.imencode(".png", annotated)
    annotated_data_url = f"data:image/png;base64,{base64.b64encode(buf).decode('ascii')}" if ok else None

    return {
        "status": "success",
        "message": "Photo saved successfully on server!",
        "scan": _json_safe(result),
        "annotated_image": annotated_data_url,
    }

@app.get("/")
def read_scan():
    return FileResponse("static/index/index.html")

@app.get("/network")
def read_network():
    return FileResponse("static/network/index.html")

@app.get("/formal_cards")
def read_cards():
    return FileResponse("static/formal_cards/index.html")

@app.get("/social_cards")
def read_cards():
    return FileResponse("static/social_cards/index.html")
