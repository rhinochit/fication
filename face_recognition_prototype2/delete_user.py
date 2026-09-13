"""Remove someone's enrollment from Supabase entirely (e.g. before
re-enrolling with a better sample) — deletes their user row and everything
referencing it (consent, face_data, profiles, prompts, scan_logs, connections).

Usage:
    python delete_user.py "Rachit"
"""
import sys

import supabase_client as sb_db


def delete_user(name):
    user_id = sb_db.find_user_by_name(name)
    if user_id is None:
        print(f"No enrolled user named '{name}'.")
        return

    sb_db.delete_user_by_id(user_id)
    print(f"Removed '{name}' from Supabase.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python delete_user.py <name>")
        sys.exit(1)
    delete_user(sys.argv[1])
