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



if __name__ == "__main__":
    init_db()
