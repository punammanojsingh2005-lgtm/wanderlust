"""
Wander — Authentication Routes
POST /api/auth/signup   — create account
POST /api/auth/login    — login, start session
POST /api/auth/logout   — clear session
GET  /api/auth/me       — return current user
"""
import bcrypt
from flask import Blueprint, request, jsonify, session
from database import get_db

auth_bp = Blueprint("auth", __name__)


def _user_dict(user):
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "is_admin": bool(user["is_admin"]),
        "created_at": user["created_at"],
    }


@auth_bp.route("/api/auth/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "All fields are required."}), 400
    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"error": "Invalid email address."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    db = get_db()
    try:
        if db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
            return jsonify({"error": "An account with this email already exists."}), 409

        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cur = db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, pw_hash),
        )
        db.commit()
        user_id = cur.lastrowid

        session["user_id"] = user_id
        session["user_name"] = name
        session["user_email"] = email
        session["is_admin"] = False

        return jsonify(
            {
                "success": True,
                "user": {"id": user_id, "name": name, "email": email, "is_admin": False},
            }
        )
    finally:
        db.close()


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    db = get_db()
    try:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not user:
            return jsonify({"error": "Invalid email or password."}), 401
        if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return jsonify({"error": "Invalid email or password."}), 401

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]
        session["is_admin"] = bool(user["is_admin"])

        return jsonify({"success": True, "user": _user_dict(user)})
    finally:
        db.close()


@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


@auth_bp.route("/api/auth/me")
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False}), 401

    db = get_db()
    try:
        user = db.execute(
            "SELECT id, name, email, is_admin, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not user:
            session.clear()
            return jsonify({"authenticated": False}), 401
        return jsonify({"authenticated": True, "user": _user_dict(user)})
    finally:
        db.close()
