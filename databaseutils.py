import sqlite3
from passlib.hash import bcrypt
from database import get_connection, get_columns

def insert_row(table: str, data: dict) -> int:
    """
    Safely insert a row into any table using a dict of column -> value.
    Returns the new row's ID.
    """
    with get_connection() as conn:
        cols = set(get_columns(conn, table))   # reuse your existing helper
        payload = {k: v for k, v in data.items() if k in cols}
        if not payload:
            raise ValueError(f"No valid columns to insert into {table}.")

        names = ", ".join(f'"{c}"' for c in payload.keys())
        qmarks = ", ".join("?" for _ in payload)
        sql = f'INSERT INTO "{table}" ({names}) VALUES ({qmarks})'

        cur = conn.execute(sql, tuple(payload.values()))
        conn.commit()
        return int(cur.lastrowid)