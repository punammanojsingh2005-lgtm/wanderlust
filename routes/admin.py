"""
Wander — Admin Routes
GET  /admin                        — admin dashboard page (is_admin required)
GET  /admin/login                  — admin login page
GET  /admin/api/stats              — aggregate stats
GET  /admin/api/bookings           — all bookings
GET  /admin/api/users              — all users
GET  /admin/api/newsletter         — subscriber list
PUT  /admin/api/bookings/<id>/status — update booking status
"""
from flask import Blueprint, jsonify, session, render_template, redirect, request
from database import get_db

admin_bp = Blueprint("admin", __name__)


def _require_admin():
    if not session.get("is_admin"):
        return True
    return False


@admin_bp.route("/admin")
def admin_panel():
    if _require_admin():
        return redirect("/admin/login")
    return render_template("admin.html", admin_name=session.get("user_name", "Admin"))


@admin_bp.route("/admin/login")
def admin_login_page():
    if session.get("is_admin"):
        return redirect("/admin")
    return render_template("admin_login.html")


@admin_bp.route("/admin/api/stats")
def admin_stats():
    if _require_admin():
        return jsonify({"error": "Admin access required."}), 403

    db = get_db()
    try:
        total_users = db.execute("SELECT COUNT(*) FROM users WHERE is_admin = 0").fetchone()[0]
        total_bookings = db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
        confirmed_bookings = db.execute(
            "SELECT COUNT(*) FROM bookings WHERE status = 'confirmed'"
        ).fetchone()[0]
        total_revenue_row = db.execute(
            "SELECT SUM(amount) FROM payments WHERE status = 'succeeded'"
        ).fetchone()[0]
        total_revenue = round(float(total_revenue_row or 0), 2)
        newsletter_count = db.execute("SELECT COUNT(*) FROM newsletter").fetchone()[0]
        total_reviews = db.execute("SELECT COUNT(*) FROM user_reviews").fetchone()[0]

        recent_bookings = db.execute(
            """
            SELECT b.*, u.name AS user_name, u.email AS user_email
            FROM   bookings b
            JOIN   users u ON u.id = b.user_id
            ORDER  BY b.created_at DESC
            LIMIT  10
            """
        ).fetchall()

        return jsonify(
            {
                "total_users": total_users,
                "total_bookings": total_bookings,
                "confirmed_bookings": confirmed_bookings,
                "total_revenue": total_revenue,
                "newsletter_count": newsletter_count,
                "total_reviews": total_reviews,
                "recent_bookings": [dict(b) for b in recent_bookings],
            }
        )
    finally:
        db.close()


@admin_bp.route("/admin/api/bookings")
def admin_bookings():
    if _require_admin():
        return jsonify({"error": "Admin access required."}), 403

    db = get_db()
    try:
        rows = db.execute(
            """
            SELECT b.*, u.name AS user_name, u.email AS user_email
            FROM   bookings b
            JOIN   users u ON u.id = b.user_id
            ORDER  BY b.created_at DESC
            """
        ).fetchall()
        return jsonify({"bookings": [dict(r) for r in rows]})
    finally:
        db.close()


@admin_bp.route("/admin/api/users")
def admin_users():
    if _require_admin():
        return jsonify({"error": "Admin access required."}), 403

    db = get_db()
    try:
        rows = db.execute(
            "SELECT id, name, email, is_admin, created_at FROM users ORDER BY created_at DESC"
        ).fetchall()
        return jsonify({"users": [dict(r) for r in rows]})
    finally:
        db.close()


@admin_bp.route("/admin/api/newsletter")
def admin_newsletter():
    if _require_admin():
        return jsonify({"error": "Admin access required."}), 403

    db = get_db()
    try:
        rows = db.execute("SELECT * FROM newsletter ORDER BY subscribed_at DESC").fetchall()
        return jsonify({"subscribers": [dict(r) for r in rows], "count": len(rows)})
    finally:
        db.close()


@admin_bp.route("/admin/api/bookings/<int:booking_id>/status", methods=["PUT"])
def update_booking_status(booking_id):
    if _require_admin():
        return jsonify({"error": "Admin access required."}), 403

    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in ("pending", "confirmed", "cancelled"):
        return jsonify({"error": "Invalid status."}), 400

    db = get_db()
    try:
        db.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
        db.commit()
        return jsonify({"success": True})
    finally:
        db.close()
