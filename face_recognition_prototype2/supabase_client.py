"""Supabase-backed data layer — the real backend, replacing db.py's local
SQLite for anything reachable from the phone app. Maps onto the actual
schema (users / consent / face_data / formal_profiles / informal_profiles /
gesture_mapping / scan_logs), not the ad hoc local one.

face_data.embedding is a pgvector column fixed at 128 dimensions — matching
dlib's native size and a teammate's already-built match_face RPC function.
CLIP produces 512-d embeddings, so every embedding that touches Supabase
(write at enrollment, read for live matching) goes through reduce_to_128()
first: a fixed random projection, not a calibrated technique. It exists
purely to fit the existing schema without altering it (which would also
affect match_face) — this is a real, unverified accuracy tradeoff, not a
free conversion. See reduce_to_128()'s docstring.

Credentials load from fication_backend/.env regardless of which script
imports this (demo.py here, or fication_backend/main.py) — SUPABASE_URL and
SUPABASE_KEY (the service_role key: full access, bypasses RLS; never the
anon key here — this is backend-only code).
"""
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import numpy as np
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "fication_backend", ".env"))

_client = None
_projection_matrix = None
_PROJECTION_SEED = 42
_PROJECTION_IN_DIM = 512
_PROJECTION_OUT_DIM = 128


def reduce_to_128(embedding_512: np.ndarray) -> np.ndarray:
    """CLIP's 512-d embedding -> a fixed 128-d random projection, so it fits
    the existing pgvector(128) column. The projection matrix is generated
    once with a fixed seed, so it's identical on every run — critical, since
    the same transform must be applied at enrollment time and at every
    identify-time comparison, or distances become meaningless. Re-normalized
    to unit length afterward so distance comparisons stay consistent with
    the rest of the pipeline's convention.
    """
    global _projection_matrix
    if _projection_matrix is None:
        rng = np.random.RandomState(_PROJECTION_SEED)
        matrix = rng.normal(size=(_PROJECTION_IN_DIM, _PROJECTION_OUT_DIM)).astype(np.float32)
        matrix /= np.linalg.norm(matrix, axis=0, keepdims=True)
        _projection_matrix = matrix

    reduced = embedding_512.astype(np.float32) @ _projection_matrix
    norm = np.linalg.norm(reduced)
    return reduced / norm if norm > 1e-6 else reduced

# gesture.py's internal labels -> this schema's actual gesture_type/target_type
# vocabulary — confirmed from the teammate's own backend code (app/main.py's
# onboarding default), not guessed: 'v_sign'/'five_fingers' and
# 'formal_profile'/'informal_profile'. The default mapping applies only when
# a user hasn't got their own gesture_mapping rows (e.g. enrolled through
# this script rather than the teammate's /users/onboard, which seeds them).
GESTURE_TYPE = {"BUSINESS": "v_sign", "INSTAGRAM": "five_fingers"}
DEFAULT_TARGET = {"BUSINESS": "formal_profile", "INSTAGRAM": "informal_profile"}


def get_client():
    global _client
    if _client is None:
        _client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    return _client


def encode_embedding(embedding: np.ndarray) -> str:
    """face_data.embedding is a pgvector `vector` column, not plain text —
    it needs the literal '[0.1,0.2,...]' text format, not base64.
    """
    return "[" + ",".join(f"{x:.8g}" for x in embedding.astype(np.float32)) + "]"


def decode_embedding(value) -> np.ndarray:
    """value: pgvector's string form '[0.1,0.2,...]' as returned by PostgREST."""
    if isinstance(value, str):
        value = value.strip("[]")
        return np.array([float(x) for x in value.split(",")], dtype=np.float32)
    return np.asarray(value, dtype=np.float32)


def _now():
    return datetime.now(timezone.utc).isoformat()


def create_user(auth_id=None):
    sb = get_client()
    resp = sb.table("users").insert({"auth_id": auth_id}).execute()
    return resp.data[0]["id"]


def create_consent(user_id, consent_type="face_enrollment", consent_method="app_submission"):
    sb = get_client()
    resp = sb.table("consent").insert({
        "user_id": user_id,
        "consent_type": consent_type,
        "consent_method": consent_method,
        "given_at": _now(),
    }).execute()
    return resp.data[0]["id"]


def save_face_data(user_id, embedding_512, consent_id):
    """embedding_512: the raw 512-d CLIP embedding — reduced to 128-d here
    before it ever reaches Supabase, so callers don't need to know about
    the projection.
    """
    sb = get_client()
    reduced = reduce_to_128(embedding_512)
    sb.table("face_data").insert({
        "user_id": user_id,
        "embedding": encode_embedding(reduced),
        "consent_id": consent_id,
        "status": "active",
        "enrolled_at": _now(),
    }).execute()


def save_formal_profile(user_id, name, **fields):
    sb = get_client()
    sb.table("formal_profiles").upsert({"user_id": user_id, "name": name, **fields}).execute()


def save_informal_profile(user_id, name, **fields):
    sb = get_client()
    sb.table("informal_profiles").upsert({"user_id": user_id, "name": name, **fields}).execute()


def load_all_face_data():
    """Returns [(user_id, name, pose_placeholder, embedding), ...] — shaped
    to match identity.best_match()'s expected 4-tuple (there's no per-pose
    column in this schema, unlike the local db.py's face_samples table;
    every enrolled embedding is just one averaged vector per user here).
    name is pulled from formal_profiles, falling back to informal_profiles.

    This runs on every photo demo.py processes, so the formal/informal
    lookups (independent of each other — both just depend on user_ids,
    already known after the first query) run concurrently on threads
    instead of as two sequential network round-trips to Supabase.
    """
    sb = get_client()
    face_rows = sb.table("face_data").select("user_id, embedding").eq("status", "active").execute().data
    if not face_rows:
        return []

    user_ids = list({r["user_id"] for r in face_rows})
    with ThreadPoolExecutor(max_workers=2) as pool:
        formal_future = pool.submit(
            lambda: sb.table("formal_profiles").select("user_id, name").in_("user_id", user_ids).execute().data
        )
        informal_future = pool.submit(
            lambda: sb.table("informal_profiles").select("user_id, name").in_("user_id", user_ids).execute().data
        )
        formal = {r["user_id"]: r["name"] for r in formal_future.result()}
        informal = {r["user_id"]: r["name"] for r in informal_future.result()}

    results = []
    for row in face_rows:
        uid = row["user_id"]
        name = formal.get(uid) or informal.get(uid) or uid
        results.append((uid, name, "unposed", decode_embedding(row["embedding"])))
    return results


def get_gesture_target(user_id, cv_gesture_label, default):
    """Looks up this user's own gesture_mapping row for this gesture; falls
    back to `default` if they haven't configured one, or it's inactive.
    cv_gesture_label is gesture.py's label ('BUSINESS'/'INSTAGRAM').
    """
    sb = get_client()
    gesture_type = GESTURE_TYPE.get(cv_gesture_label)
    if gesture_type is None:
        return default
    resp = (
        sb.table("gesture_mapping")
        .select("target_type")
        .eq("user_id", user_id)
        .eq("gesture_type", gesture_type)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    return resp.data[0]["target_type"] if resp.data else default


def get_or_create_user_by_name(name):
    """Looks up an existing user by name in formal_profiles (falling back to
    informal_profiles); creates a new user if none exists. Mirrors the old
    local db.py's get_or_create_user, so re-running enroll.py for the same
    person updates them instead of creating a duplicate.
    """
    existing = find_user_by_name(name)
    if existing:
        return existing

    user_id = create_user()
    save_formal_profile(user_id, name=name)
    save_informal_profile(user_id, name=name)
    return user_id


def find_user_by_name(name):
    sb = get_client()
    rows = sb.table("formal_profiles").select("user_id").eq("name", name).limit(1).execute().data
    if rows:
        return rows[0]["user_id"]
    rows = sb.table("informal_profiles").select("user_id").eq("name", name).limit(1).execute().data
    return rows[0]["user_id"] if rows else None


def clear_face_data(user_id):
    """Removes all of a user's stored face samples — called before
    re-enrolling someone, so repeated enroll.py runs replace rather than
    accumulate redundant samples.
    """
    sb = get_client()
    sb.table("face_data").delete().eq("user_id", user_id).execute()


def list_users():
    """Returns [(user_id, name, sample_count, created_at), ...] for everyone enrolled."""
    sb = get_client()
    users = sb.table("users").select("id, created_at").order("created_at").execute().data
    if not users:
        return []

    user_ids = [u["id"] for u in users]
    formal = {r["user_id"]: r["name"] for r in
              sb.table("formal_profiles").select("user_id, name").in_("user_id", user_ids).execute().data}
    informal = {r["user_id"]: r["name"] for r in
                sb.table("informal_profiles").select("user_id, name").in_("user_id", user_ids).execute().data}
    face_rows = sb.table("face_data").select("user_id").in_("user_id", user_ids).execute().data
    counts = {}
    for r in face_rows:
        counts[r["user_id"]] = counts.get(r["user_id"], 0) + 1

    results = []
    for u in users:
        uid = u["id"]
        name = formal.get(uid) or informal.get(uid) or "(no profile)"
        results.append((uid, name, counts.get(uid, 0), u["created_at"]))
    return results


def load_all_gesture_mappings():
    """Returns {(user_id, gesture_type): target_type} for every active
    mapping in one query. demo.py caches this and refreshes it periodically
    instead of calling get_gesture_target() per scan — that was one of
    several sequential Supabase round-trips stacking up on the hot path.
    """
    sb = get_client()
    rows = (
        sb.table("gesture_mapping")
        .select("user_id, gesture_type, target_type")
        .eq("is_active", True)
        .execute()
        .data
    )
    return {(r["user_id"], r["gesture_type"]): r["target_type"] for r in rows}


def delete_user_by_id(user_id):
    """Deletes a user and everything referencing them. Explicit per-table
    deletes rather than relying on ON DELETE CASCADE actually being set up
    the way this code assumes — safer to be sure.
    """
    sb = get_client()
    sb.table("scan_logs").delete().eq("scanned_user_id", user_id).execute()
    sb.table("connections").delete().eq("scanner_user_id", user_id).execute()
    sb.table("connections").delete().eq("scanned_user_id", user_id).execute()
    sb.table("gesture_mapping").delete().eq("user_id", user_id).execute()
    sb.table("profile_prompts").delete().eq("user_id", user_id).execute()
    sb.table("face_data").delete().eq("user_id", user_id).execute()
    sb.table("formal_profiles").delete().eq("user_id", user_id).execute()
    sb.table("informal_profiles").delete().eq("user_id", user_id).execute()
    sb.table("consent").delete().eq("user_id", user_id).execute()
    sb.table("users").delete().eq("id", user_id).execute()


def save_scan_log(scanned_user_id, cv_gesture_label, distance):
    """distance is Euclidean (lower = better match); scan_logs wants a
    confidence_score (higher = better), so this is a simple 0..1 approximation,
    not a calibrated probability.
    """
    sb = get_client()
    confidence = max(0.0, 1.0 - distance)
    sb.table("scan_logs").insert({
        "scanned_user_id": scanned_user_id,
        "gesture_detected": GESTURE_TYPE.get(cv_gesture_label, "none"),
        "confidence_score": confidence,
        "created_at": _now(),
    }).execute()


def get_latest_reveal(user_id=None):
    """Reads from the latest_reveals view (the else-if join over scan_logs +
    formal_profiles/informal_profiles) — this is what the frontend actually
    wants to render: one row with either the formal_* or informal_* fields
    populated, never both. Pass user_id to scope it to one person; omit for
    the single most recent reveal across everyone.
    """
    sb = get_client()
    q = sb.table("latest_reveals").select("*").order("created_at", desc=True).limit(1)
    if user_id:
        q = q.eq("scanned_user_id", user_id)
    rows = q.execute().data
    return rows[0] if rows else None
