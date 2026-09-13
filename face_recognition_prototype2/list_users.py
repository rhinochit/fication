"""List everyone currently enrolled in Supabase, and how many face samples
each has on file.

Usage:
    python list_users.py
"""
import supabase_client as sb_db


def main():
    rows = sb_db.list_users()
    if not rows:
        print("No one enrolled yet.")
        return

    print(f"{'ID':<38} {'Name':<20} {'Samples':<8} Enrolled at")
    for user_id, name, sample_count, created_at in rows:
        print(f"{user_id:<38} {name:<20} {sample_count:<8} {created_at}")


if __name__ == "__main__":
    main()
