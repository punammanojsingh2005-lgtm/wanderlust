"""
Wander — Booking Routes
POST   /api/bookings                    — create booking
GET    /api/bookings                    — list user's bookings
DELETE /api/bookings/<id>              — cancel booking
POST   /api/bookings/<id>/confirm      — confirm after payment
"""
import os
import math
import pandas as pd
from flask import Blueprint, request, jsonify, session
from database import get_db

bookings_bp = Blueprint("bookings", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def _require_auth():
    if "user_id" not in session:
        return jsonify({"error": "Authentication required."}), 401
    return None


def _row_to_dict(row):
    d = dict(row)
    return {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in d.items()}


@bookings_bp.route("/api/bookings", methods=["GET"])
def get_bookings():
    err = _require_auth()
    if err:
        return err

    db = get_db()
    try:
        rows = db.execute(
            """
            SELECT b.*,
                   p.status       AS payment_status,
                   p.amount       AS paid_amount,
                   p.stripe_payment_id
            FROM   bookings b
            LEFT JOIN payments p ON p.booking_id = b.id
            WHERE  b.user_id = ?
            ORDER  BY b.created_at DESC
            """,
            (session["user_id"],),
        ).fetchall()
        return jsonify({"bookings": [dict(r) for r in rows]})
    finally:
        db.close()


@bookings_bp.route("/api/bookings", methods=["POST"])
def create_booking():
    err = _require_auth()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    dest_id = data.get("destination_id")
    travel_date = data.get("travel_date")
    num_guests = int(data.get("num_guests", 1))

    if not dest_id or not travel_date:
        return jsonify({"error": "destination_id and travel_date are required."}), 400

    # Load destination from CSV
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, "destinations.csv"))
        row = df[df["id"] == int(dest_id)]
        if row.empty:
            return jsonify({"error": "Destination not found."}), 404
        dest = row.iloc[0]
        total_amount = float(dest["avg_cost_per_person"]) * num_guests
        dest_name = str(dest["city"])
        dest_image = str(dest["image_url"])
        dest_country = str(dest["country"])
    except Exception as exc:
        return jsonify({"error": f"Failed to load destination: {exc}"}), 500

    db = get_db()
    try:
        cur = db.execute(
            """
            INSERT INTO bookings
                (user_id, destination_id, destination_name, destination_image,
                 destination_country, travel_date, num_guests, total_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                dest_id,
                dest_name,
                dest_image,
                dest_country,
                travel_date,
                num_guests,
                total_amount,
                "pending",
            ),
        )
        db.commit()
        return jsonify(
            {
                "success": True,
                "booking_id": cur.lastrowid,
                "total_amount": total_amount,
                "destination": dest_name,
            }
        )
    finally:
        db.close()


@bookings_bp.route("/api/bookings/<int:booking_id>", methods=["DELETE"])
def cancel_booking(booking_id):
    err = _require_auth()
    if err:
        return err

    db = get_db()
    try:
        booking = db.execute(
            "SELECT id FROM bookings WHERE id = ? AND user_id = ?",
            (booking_id, session["user_id"]),
        ).fetchone()
        if not booking:
            return jsonify({"error": "Booking not found."}), 404

        db.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE id = ?", (booking_id,)
        )
        db.commit()
        return jsonify({"success": True, "message": "Booking cancelled."})
    finally:
        db.close()


@bookings_bp.route("/api/bookings/<int:booking_id>/confirm", methods=["POST"])
def confirm_booking(booking_id):
    err = _require_auth()
    if err:
        return err

    db = get_db()
    try:
        db.execute(
            "UPDATE bookings SET status = 'confirmed' WHERE id = ? AND user_id = ?",
            (booking_id, session["user_id"]),
        )
        db.commit()
        return jsonify({"success": True})
    finally:
        db.close()
