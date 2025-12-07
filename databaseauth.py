import sqlite3
from passlib.hash import bcrypt
from database import get_connection

def get_user_by_email(email: str):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.strip().lower(),)
        ).fetchone()
    return row  # Row object (dict-like) or None


def create_user(email: str, password: str) -> int:
    """
    Create a user and return the new user id.
    Raises sqlite3.IntegrityError if email already exists.
    """
    email_norm = email.strip().lower()
    pw_hash = bcrypt.hash(password)

    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email_norm, pw_hash),
        )
        conn.commit()
        return int(cur.lastrowid)


def verify_user(email: str, password: str):
    """
    Returns the user row if the email/password are correct, otherwise None.
    """
    user = get_user_by_email(email)
    if user is None:
        return None

    if not bcrypt.verify(password, user["password_hash"]):
        return None

    return user  # correct credentials
