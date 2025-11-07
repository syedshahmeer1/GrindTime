import sqlite3
from datetime import datetime, date


# Connection and initializaton 
def get_connection():
    conn = sqlite3.connect("grindtime.db")
    conn.row_factory = sqlite3.Row  # lets you access columns by name
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    with open("schema.sql", "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("Database initialized")

# Testing and Listing
def get_tables(conn: sqlite3.Connection) -> list[str]:
    cur = conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    return [r["name"] for r in cur.fetchall()]

def get_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    cur = conn.execute(f'PRAGMA table_info("{table}")')
    rows = cur.fetchall()
    if not rows:
        raise ValueError(f'Table "{table}" not found.')
    return [r["name"] for r in rows]

def count_rows(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f'SELECT COUNT(*) AS c FROM "{table}"').fetchone()["c"]

def sample_rows(conn: sqlite3.Connection, table: str, limit: int = 5) -> list[sqlite3.Row]:
    return conn.execute(f'SELECT * FROM "{table}" LIMIT ?', (limit,)).fetchall()


if __name__ == "__main__":
    init_db()
