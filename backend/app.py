from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
import sqlite3

app = Flask(__name__)
CORS(app)  # enable CORS for all routes (fine for dev)


DB_PATH = Path(__file__).resolve().parent.parent / "grindtime.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"success": False, "message": "Missing email or password"}), 400

    with get_db() as conn:
        cur = conn.execute(
            "SELECT password_hash FROM users WHERE email = ?",
            (email,)
        )
        row = cur.fetchone()

    if row is None:
        return jsonify({"success": False, "message": "User not found"}), 401

    # For now we’re treating password_hash as plain text.
    if row["password_hash"] != password:
        return jsonify({"success": False, "message": "Incorrect password"}), 401

    return jsonify({"success": True, "message": "Login successful"}), 200

if __name__ == "__main__":
    app.run(debug=True)
