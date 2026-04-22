"""
Wander — Payment Routes (Stripe + Demo fallback)
POST /api/payment/create-intent  — create PaymentIntent
POST /api/payment/confirm         — persist payment after success
GET  /api/payments                — user payment history
"""
import uuid
from flask import Blueprint, request, jsonify, session
from database import get_db
from config import Config

payments_bp = Blueprint("payments", __name__)


def _require_auth():
    if "user_id" not in session:
        return jsonify({"error": "Authentication required."}), 401
    return None


@payments_bp.route("/api/payment/create-intent", methods=["POST"])
def create_payment_intent():
    err = _require_auth()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    booking_id = data.get("booking_id")
    amount = data.get("amount")  # USD dollars

    if not booking_id or not amount:
        return jsonify({"error": "booking_id and amount are required."}), 400

    db = get_db()
    try:
        booking = db.execute(
            "SELECT * FROM bookings WHERE id = ? AND user_id = ?",
            (booking_id, session["user_id"]),
        ).fetchone()
        if not booking:
            return jsonify({"error": "Booking not found."}), 404

        # ── Demo mode — skip real Stripe call ──────────────────────────────
        if Config.STRIPE_DEMO_MODE or Config.STRIPE_SECRET_KEY in ("sk_test_demo", ""):
            fake_id = f"pi_demo_{uuid.uuid4().hex[:16]}"
            # Save a pending payment record
            db.execute(
                """INSERT INTO payments
                       (booking_id, user_id, stripe_payment_id, amount, status)
                   VALUES (?, ?, ?, ?, ?)""",
                (booking_id, session["user_id"], fake_id, amount, "pending"),
            )
            db.commit()
            return jsonify(
                {
                    "client_secret": f"{fake_id}_secret_demo",
                    "payment_intent_id": fake_id,
                    "demo_mode": True,
                }
            )

        # ── Real Stripe ─────────────────────────────────────────────────────
        import stripe
        stripe.api_key = Config.STRIPE_SECRET_KEY

        try:
            intent = stripe.PaymentIntent.create(
                amount=int(float(amount) * 100),
                currency="usd",
                metadata={"booking_id": booking_id, "user_id": session["user_id"]},
            )
            db.execute(
                """INSERT INTO payments
                       (booking_id, user_id, stripe_payment_id, amount, status)
                   VALUES (?, ?, ?, ?, ?)""",
                (booking_id, session["user_id"], intent.id, amount, "pending"),
            )
            db.commit()
            return jsonify(
                {"client_secret": intent.client_secret, "payment_intent_id": intent.id}
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@payments_bp.route("/api/payment/confirm", methods=["POST"])
def confirm_payment():
    err = _require_auth()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    payment_intent_id = data.get("payment_intent_id")
    booking_id = data.get("booking_id")

    if not payment_intent_id or not booking_id:
        return jsonify({"error": "payment_intent_id and booking_id are required."}), 400

    db = get_db()
    try:
        db.execute(
            "UPDATE payments SET status = 'succeeded' WHERE stripe_payment_id = ? AND user_id = ?",
            (payment_intent_id, session["user_id"]),
        )
        db.execute(
            "UPDATE bookings SET status = 'confirmed' WHERE id = ? AND user_id = ?",
            (booking_id, session["user_id"]),
        )
        db.commit()
        return jsonify({"success": True, "message": "Booking confirmed!"})
    finally:
        db.close()


@payments_bp.route("/api/payments", methods=["GET"])
def get_payments():
    err = _require_auth()
    if err:
        return err

    db = get_db()
    try:
        rows = db.execute(
            """
            SELECT p.*, b.destination_name, b.travel_date, b.num_guests
            FROM   payments p
            LEFT JOIN bookings b ON b.id = p.booking_id
            WHERE  p.user_id = ?
            ORDER  BY p.created_at DESC
            """,
            (session["user_id"],),
        ).fetchall()
        return jsonify({"payments": [dict(r) for r in rows]})
    finally:
        db.close()
