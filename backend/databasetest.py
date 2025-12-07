import sqlite3
from datetime import datetime, date

from database import (
    get_connection, init_db, get_tables, get_columns, count_rows, sample_rows
)

# insert rows safely
def insert_row(conn: sqlite3.Connection, table: str, data: dict) -> int:
    cols = set(get_columns(conn, table))
    payload = {k: v for k, v in data.items() if k in cols}
    if not payload:
        raise ValueError(f"No valid columns to insert into {table}.")
    names = ", ".join(f'"{c}"' for c in payload.keys())
    qmarks = ", ".join("?" for _ in payload)
    sql = f'INSERT INTO "{table}" ({names}) VALUES ({qmarks})'
    cur = conn.execute(sql, tuple(payload.values()))
    conn.commit()
    return int(cur.lastrowid)

def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return name in get_tables(conn)

# seeding tests
def seed_all(conn: sqlite3.Connection) -> dict:
    """
    Inserts exactly one row into each table that exists in the schema,
    sets up foreign keys correctly. Returns ids for reference.
    """
    ids = {"user_id": None, "session_id": None}

    now = datetime.utcnow().isoformat(timespec="seconds")
    today = date.today().isoformat()

    # users
    if table_exists(conn, "users"):
        email = f"test+{now.replace(':','').replace('-','').replace('T','_')}@example.com"
        ids["user_id"] = insert_row(conn, "users", {
            "email": email,
            "password_hash": "dummyhash",
            "created_at": now,
        })
        print(f"users.id={ids['user_id']}")
    else:
        print("filling users failed")

    # user_profiles
    if ids["user_id"] and table_exists(conn, "user_profiles"):
        insert_row(conn, "user_profiles", {
            "user_id": ids["user_id"],
            "display_name": "Seed User",
            "sex": "other",
            "dob": "2000-01-01",
            "height_cm": 180.0,
            "weight_kg": 80.0,
            "activity_factor": 1.55,
            "experience_level": "intermediate",
        })
        print("user_profiles filled")

    # body_metrics
    if ids["user_id"] and table_exists(conn, "body_metrics"):
        insert_row(conn, "body_metrics", {
            "user_id": ids["user_id"],
            "measured_at": today,
            "weight_kg": 80.5,
            "bodyfat_pct": 14.2,
            "chest_cm": 105.0,
            "waist_cm": 82.0,
            "hips_cm": 98.0,
        })
        print("body_metrics filled")

    # exercise_prs
    if ids["user_id"] and table_exists(conn, "exercise_prs"):
        insert_row(conn, "exercise_prs", {
            "user_id": ids["user_id"],
            "exercise_name": "Bench Press",
            "pr_type": "1RM",
            "value": 140.0,
            "achieved_at": now,
            "notes": "seed",
        })
        print("exercise_prs filled")

    # nutrition_entries
    if ids["user_id"] and table_exists(conn, "nutrition_entries"):
        insert_row(conn, "nutrition_entries", {
            "user_id": ids["user_id"],
            "eaten_at": now,
            "fdc_id": None,
            "serving_qty": 1.0,
            "serving_unit": "serving",
            "calories": 500,
            "protein_g": 35,
            "carbs_g": 40,
            "fat_g": 20,
            "notes": "seed meal",
        })
        print("nutrition_entries filled")

    # macro_targets
    if ids["user_id"] and table_exists(conn, "macro_targets"):
        insert_row(conn, "macro_targets", {
            "user_id": ids["user_id"],
            "effective_from": today,
            "goal": "maintain",
            "kcal": 2600,
            "protein_g": 180,
            "carbs_g": 280,
            "fat_g": 70,
        })
        print("macro_targets filled")

    # workout_sessions
    if ids["user_id"] and table_exists(conn, "workout_sessions"):
        ids["session_id"] = insert_row(conn, "workout_sessions", {
            "user_id": ids["user_id"],
            "started_at": now,
            "ended_at": now,
            "notes": "seed session",
        })
        print(f"workout_sessions.id={ids['session_id']}")

    # workout_sets
    if ids.get("session_id") and table_exists(conn, "workout_sets"):
        insert_row(conn, "workout_sets", {
            "session_id": ids["session_id"],
            "exercise_name": "Bench Press",
            "set_index": 1,
            "reps": 5,
            "weight_kg": 100.0,
            "rpe": 8.0,
            "rest_seconds": 180,
            "is_warmup": 0,
        })
        print("workout_sets filled")

    return ids

# printing helpers
def print_counts(conn: sqlite3.Connection, header: str) -> None:
    print(f"\n-- {header} --")
    for t in get_tables(conn):
        print(f"{t:22s} {count_rows(conn, t):5d}")
    print("-- end --\n")

def print_all_rows(conn: sqlite3.Connection) -> None:
    tables = get_tables(conn)
    if not tables:
        print("No tables found.")
        return
    print("\n===== ALL ROWS =====")
    for t in tables:
        rows = conn.execute(f'SELECT * FROM "{t}"').fetchall()
        print(f"\n[{t}] ({len(rows)} rows)")
        for i, r in enumerate(rows, 1):
            print(f"  #{i}: " + ", ".join(f"{k}={repr(r[k])}" for k in r.keys()))
    print("\n====================\n")

# delete all data
def delete_all_data(conn: sqlite3.Connection) -> None:
    tables = get_tables(conn)
    if "users" in tables:
        # preview before deletion (lists all rows per spec)
        print("\nall tables before deleting data:")
        print_all_rows(conn)
        conn.execute('DELETE FROM "users"')
        conn.commit()
        print("Deleted all users.")

# main function
def main():
    # Initialize schema
    init_db()

    with get_connection() as conn:
        # seed one entry per table
        seed_all(conn)

        # list counts per table
        print_counts(conn, "COUNTS AFTER SEED")

        # list all rows per table
        print_all_rows(conn)

        # delete all data
        delete_all_data(conn)

        # reprint counts
        print_counts(conn, "COUNTS AFTER DELETE")

if __name__ == "__main__":
    main()