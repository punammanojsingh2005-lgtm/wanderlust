"""
Wander — User Reviews Routes
POST /api/user-reviews        — submit a review (auth required)
GET  /api/user-reviews/<id>   — get reviews for a destination
"""
from flask import Blueprint, request, jsonify, session
from database import get_db

reviews_bp = Blueprint("reviews", __name__)


def _require_auth():
    if "user_id" not in session:
        return jsonify({"error": "Authentication required."}), 401
    return None


@reviews_bp.route("/api/user-reviews", methods=["POST"])
def post_review():
    err = _require_auth()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    dest_id = data.get("destination_id")
    rating = data.get("rating")
    review_text = data.get("review_text", "").strip()

    if not dest_id or not rating or not review_text:
        return jsonify({"error": "destination_id, rating, and review_text are required."}), 400

    try:
        rating = int(rating)
        assert 1 <= rating <= 5
    except (ValueError, AssertionError):
        return jsonify({"error": "Rating must be an integer between 1 and 5."}), 400

    db = get_db()
    try:
        existing = db.execute(
            "SELECT id FROM user_reviews WHERE user_id = ? AND destination_id = ?",
            (session["user_id"], dest_id),
        ).fetchone()
        if existing:
            return jsonify({"error": "You have already reviewed this destination."}), 409

        db.execute(
            "INSERT INTO user_reviews (user_id, destination_id, rating, review_text) VALUES (?, ?, ?, ?)",
            (session["user_id"], dest_id, rating, review_text),
        )
        db.commit()
        return jsonify({"success": True, "message": "Review submitted — thank you!"})
    finally:
        db.close()


@reviews_bp.route("/api/user-reviews/<int:dest_id>", methods=["GET"])
def get_dest_reviews(dest_id):
    db = get_db()
    try:
        rows = db.execute(
            """
            SELECT ur.id, ur.rating, ur.review_text, ur.created_at, u.name AS reviewer_name
            FROM   user_reviews ur
            JOIN   users u ON u.id = ur.user_id
            WHERE  ur.destination_id = ?
            ORDER  BY ur.created_at DESC
            """,
            (dest_id,),
        ).fetchall()
        return jsonify({"reviews": [dict(r) for r in rows]})
    finally:
        db.close()
