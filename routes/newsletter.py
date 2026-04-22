"""
Wander — Newsletter Route (DB-persisted, duplicate-safe)
POST /api/newsletter
"""
from flask import Blueprint, request, jsonify
from database import get_db

newsletter_bp = Blueprint("newsletter", __name__)


@newsletter_bp.route("/api/newsletter", methods=["POST"])
def newsletter_signup():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()

    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"error": "Please provide a valid email address."}), 400

    db = get_db()
    try:
        if db.execute("SELECT id FROM newsletter WHERE email = ?", (email,)).fetchone():
            return jsonify({"error": "This email is already subscribed — no duplicates here!"}), 409

        db.execute("INSERT INTO newsletter (email) VALUES (?)", (email,))
        db.commit()
        return jsonify(
            {
                "success": True,
                "message": f"Welcome aboard! {email} has been subscribed to the Wander travel edit.",
            }
        )
    finally:
        db.close()
