"""
Wander — Luxury Travel Guide API  (Full-Stack Edition)
Flask backend: auth + bookings + payments + reviews + newsletter + admin
"""
import os
import math
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# ── App Setup ─────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

app = Flask(
    __name__,
    static_folder=".",
    static_url_path="",
    template_folder="templates",
)
CORS(app, supports_credentials=True)

# ── Configuration ──────────────────────────────────────────────────────────────
from config import Config

app.config["SECRET_KEY"] = Config.SECRET_KEY
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False  # True in production (HTTPS)

# ── Database ───────────────────────────────────────────────────────────────────
from database import init_db

with app.app_context():
    init_db()

# ── Blueprints ─────────────────────────────────────────────────────────────────
from routes.auth import auth_bp
from routes.bookings import bookings_bp
from routes.payments import payments_bp
from routes.reviews import reviews_bp
from routes.newsletter import newsletter_bp
from routes.admin import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(bookings_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(newsletter_bp)
app.register_blueprint(admin_bp)


# ── Helpers ────────────────────────────────────────────────────────────────────
def load_destinations():
    return pd.read_csv(os.path.join(DATA_DIR, "destinations.csv"))


def load_reviews():
    return pd.read_csv(os.path.join(DATA_DIR, "reviews.csv"))


def load_experiences():
    return pd.read_csv(os.path.join(DATA_DIR, "experiences.csv"))


def row_to_dict(row):
    d = row.to_dict()
    return {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in d.items()}


# ── Serve Frontend ─────────────────────────────────────────────────────────────
@app.route("/")
def serve_index():
    return send_from_directory(".", "index.html")


# ── Destinations ───────────────────────────────────────────────────────────────
@app.route("/api/destinations")
def get_destinations():
    """
    GET /api/destinations
    Params: continent, category, search, min_cost, max_cost, sort, order, limit
    """
    df = load_destinations()

    continent = request.args.get("continent")
    if continent:
        df = df[df["continent"].str.lower() == continent.lower()]

    category = request.args.get("category")
    if category:
        df = df[df["category"].str.lower() == category.lower()]

    search = request.args.get("search")
    if search:
        s = search.lower()
        df = df[
            df["city"].str.lower().str.contains(s)
            | df["country"].str.lower().str.contains(s)
            | df["tagline"].str.lower().str.contains(s)
        ]

    min_cost = request.args.get("min_cost", type=float)
    max_cost = request.args.get("max_cost", type=float)
    if min_cost is not None:
        df = df[df["avg_cost_per_person"] >= min_cost]
    if max_cost is not None:
        df = df[df["avg_cost_per_person"] <= max_cost]

    sort_by = request.args.get("sort", "rating")
    order = request.args.get("order", "desc")
    sort_col = {"rating": "rating", "cost": "avg_cost_per_person", "reviews": "review_count"}.get(
        sort_by, "rating"
    )
    df = df.sort_values(sort_col, ascending=(order.lower() == "asc"))

    limit = request.args.get("limit", type=int)
    if limit:
        df = df.head(limit)

    destinations = []
    for _, row in df.iterrows():
        d = row_to_dict(row)
        acts = d.get("popular_activities", "")
        d["popular_activities"] = [a.strip() for a in acts.split(";")] if acts else []
        destinations.append(d)

    return jsonify({"count": len(destinations), "destinations": destinations})


@app.route("/api/destinations/<int:dest_id>")
def get_destination(dest_id):
    """Single destination with enriched data: reviews, tips, food, budget."""
    df = load_destinations()
    row = df[df["id"] == dest_id]
    if row.empty:
        return jsonify({"error": "Destination not found"}), 404

    dest = row_to_dict(row.iloc[0])
    acts = dest.get("popular_activities", "")
    dest["popular_activities"] = [a.strip() for a in acts.split(";")] if acts else []

    # CSV reviews
    rev_df = load_reviews()
    dest_revs = rev_df[rev_df["destination_id"] == dest_id]
    dest["reviews"] = [row_to_dict(r) for _, r in dest_revs.iterrows()]

    # Travel tips by category
    tips_map = {
        "Beach": [
            "🌊 Book water sports in advance during peak season",
            "🧴 Pack reef-safe sunscreen to protect coral reefs",
            "🌅 Early morning is best for crowd-free beaches",
            "💧 Stay hydrated — the sea breeze is deceptively cooling",
        ],
        "Culture": [
            "🎫 Pre-book museum tickets to skip the queues",
            "👗 Dress modestly when entering religious sites",
            "🗣️ Learn 5 basic phrases in the local language",
            "🕐 Many cultural attractions close on Mondays",
        ],
        "Mountains": [
            "🥾 Break in hiking boots before the trip",
            "🌡️ Temperatures drop ~6°C per 1,000m elevation",
            "💊 Carry altitude sickness medication if above 2,500m",
            "🎒 Pack layers — alpine weather changes fast",
        ],
        "Adventure": [
            "🛡️ Always book with certified, safety-rated operators",
            "🏥 Verify your travel insurance covers adventure activities",
            "📱 Download offline maps before heading into remote areas",
            "🌤️ Morning departures have clearer skies and calmer conditions",
        ],
        "Romance": [
            "🌹 Book romantic dinners at least two weeks in advance",
            "🛏️ Request room upgrades at hotel check-in",
            "📸 Golden hour (1 hr before sunset) is magical for photos",
            "💐 Fresh local flowers make wonderful spontaneous gifts",
        ],
    }
    category = dest.get("category", "Culture")
    dest["travel_tips"] = tips_map.get(category, tips_map["Culture"])

    # Local food by country
    food_map = {
        "Italy": ["Pizza Napoletana", "Fresh pasta al pomodoro", "Gelato artigianale", "Tiramisu"],
        "Japan": ["Ramen", "Sushi omakase", "Yakitori", "Matcha desserts"],
        "Greece": ["Fresh moussaka", "Grilled octopus", "Spanakopita", "Loukoumades"],
        "Indonesia": ["Nasi goreng", "Satay", "Gado-gado", "Babi guling"],
        "Switzerland": ["Cheese fondue", "Rösti", "Raclette", "Zürcher Geschnetzeltes"],
        "Morocco": ["Tagine", "Couscous royale", "Harira soup", "Bastilla"],
        "Argentina": ["Asado", "Empanadas", "Dulce de leche crepes", "Mate"],
        "Maldives": ["Garudhiya fish soup", "Mas huni", "Coconut sambal", "Bis keemiya"],
        "South Africa": ["Cape Malay curry", "Braai", "Biltong", "Malva pudding"],
        "Iceland": ["Lamb soup", "Skyr", "Fresh lobster", "Plokkfiskur"],
    }
    dest["local_foods"] = food_map.get(
        dest.get("country", ""),
        ["Local traditional cuisine", "Street food markets", "Chef's tasting menus", "Regional specialties"],
    )

    # Budget breakdown (percentages of avg cost per person)
    cost = dest.get("avg_cost_per_person", 2000)
    dest["budget_breakdown"] = {
        "accommodation": round(cost * 0.40),
        "food": round(cost * 0.20),
        "activities": round(cost * 0.25),
        "transport": round(cost * 0.15),
    }

    return jsonify(dest)


# ── Experiences ────────────────────────────────────────────────────────────────
@app.route("/api/experiences")
def get_experiences():
    df = load_experiences()
    category = request.args.get("category")
    if category:
        df = df[df["category"].str.lower() == category.lower()]
    df = df.sort_values("experience_count", ascending=False)
    return jsonify({"count": len(df), "experiences": [row_to_dict(r) for _, r in df.iterrows()]})


# ── Reviews (CSV) ──────────────────────────────────────────────────────────────
@app.route("/api/reviews")
def get_reviews():
    df = load_reviews()
    dest_id = request.args.get("destination_id", type=int)
    if dest_id:
        df = df[df["destination_id"] == dest_id]
    min_rating = request.args.get("min_rating", type=float)
    if min_rating:
        df = df[df["rating"] >= min_rating]
    df = df.sort_values("rating", ascending=False)
    limit = request.args.get("limit", type=int)
    if limit:
        df = df.head(limit)
    return jsonify({"count": len(df), "reviews": [row_to_dict(r) for _, r in df.iterrows()]})


# ── Stats ──────────────────────────────────────────────────────────────────────
@app.route("/api/stats")
def get_stats():
    dest_df = load_destinations()
    rev_df = load_reviews()
    exp_df = load_experiences()
    return jsonify(
        {
            "total_destinations": len(dest_df),
            "total_reviews": len(rev_df),
            "total_experiences": int(exp_df["experience_count"].sum()),
            "avg_rating": round(float(dest_df["rating"].mean()), 2),
            "continents_covered": int(dest_df["continent"].nunique()),
            "countries_covered": int(dest_df["country"].nunique()),
            "price_range": {
                "min": int(dest_df["avg_cost_per_person"].min()),
                "max": int(dest_df["avg_cost_per_person"].max()),
                "avg": int(dest_df["avg_cost_per_person"].mean()),
            },
            "top_categories": dest_df["category"].value_counts().to_dict(),
            "destinations_by_continent": dest_df["continent"].value_counts().to_dict(),
        }
    )


# ── Search ─────────────────────────────────────────────────────────────────────
@app.route("/api/search")
def search():
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify({"error": "Please provide a search query."}), 400

    dest_df = load_destinations()
    dest_matches = dest_df[
        dest_df["city"].str.lower().str.contains(q)
        | dest_df["country"].str.lower().str.contains(q)
        | dest_df["tagline"].str.lower().str.contains(q)
        | dest_df["description"].str.lower().str.contains(q)
    ]
    exp_df = load_experiences()
    exp_matches = exp_df[
        exp_df["name"].str.lower().str.contains(q)
        | exp_df["description"].str.lower().str.contains(q)
    ]
    return jsonify(
        {
            "query": q,
            "destinations": [row_to_dict(r) for _, r in dest_matches.iterrows()],
            "experiences": [row_to_dict(r) for _, r in exp_matches.iterrows()],
            "total_results": len(dest_matches) + len(exp_matches),
        }
    )


# ── AI-style Recommendation ────────────────────────────────────────────────────
@app.route("/api/recommend")
def recommend():
    """
    GET /api/recommend?budget=3000&category=Beach
    Scores destinations on rating (70%) + value (30%).
    """
    budget = request.args.get("budget", type=int)
    category = request.args.get("category", "")

    df = load_destinations()
    if budget:
        df = df[df["avg_cost_per_person"] <= budget]
    if category:
        df = df[df["category"].str.lower() == category.lower()]

    if df.empty:
        return jsonify({"count": 0, "destinations": []})

    df = df.copy()
    if budget and budget > 0:
        df["_value"] = 1 - (df["avg_cost_per_person"] / budget).clip(0, 1)
        df["_score"] = (df["rating"] / 5) * 0.7 + df["_value"] * 0.3
    else:
        df["_score"] = df["rating"] / 5

    df = df.sort_values("_score", ascending=False).head(3)

    destinations = []
    for _, row in df.iterrows():
        d = row_to_dict(row)
        acts = d.get("popular_activities", "")
        d["popular_activities"] = [a.strip() for a in acts.split(";")] if acts else []
        d.pop("_score", None)
        d.pop("_value", None)
        destinations.append(d)

    return jsonify({"count": len(destinations), "destinations": destinations})


# ── Saved Destinations ─────────────────────────────────────────────────────────
from flask import session as flask_session
from database import get_db


@app.route("/api/saved", methods=["GET"])
def get_saved():
    if "user_id" not in flask_session:
        return jsonify({"error": "Authentication required."}), 401
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM saved_destinations WHERE user_id = ? ORDER BY saved_at DESC",
            (flask_session["user_id"],),
        ).fetchall()
        return jsonify({"saved": [dict(r) for r in rows]})
    finally:
        db.close()


@app.route("/api/saved", methods=["POST"])
def toggle_saved():
    if "user_id" not in flask_session:
        return jsonify({"error": "Authentication required."}), 401

    data = request.get_json(silent=True) or {}
    dest_id = data.get("destination_id")
    if not dest_id:
        return jsonify({"error": "destination_id required."}), 400

    df = load_destinations()
    row = df[df["id"] == int(dest_id)]
    if row.empty:
        return jsonify({"error": "Destination not found."}), 404
    dest = row.iloc[0]

    db = get_db()
    try:
        existing = db.execute(
            "SELECT id FROM saved_destinations WHERE user_id = ? AND destination_id = ?",
            (flask_session["user_id"], dest_id),
        ).fetchone()
        if existing:
            db.execute(
                "DELETE FROM saved_destinations WHERE user_id = ? AND destination_id = ?",
                (flask_session["user_id"], dest_id),
            )
            db.commit()
            return jsonify({"success": True, "saved": False})
        else:
            db.execute(
                """INSERT INTO saved_destinations
                       (user_id, destination_id, destination_name, destination_image, destination_country)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    flask_session["user_id"],
                    dest_id,
                    str(dest["city"]),
                    str(dest["image_url"]),
                    str(dest["country"]),
                ),
            )
            db.commit()
            return jsonify({"success": True, "saved": True})
    finally:
        db.close()


# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    debug_mode = os.environ.get("FLASK_ENV") != "production"

    print("\n  🌍  Wander Travel Guide — Full-Stack Edition")
    print("  ───────────────────────────────────────────────")
    print(f"  Frontend:   http://localhost:{port}")
    print(f"  Admin:      http://localhost:{port}/admin  (admin@wander.com / admin123)")
    print(f"  API:        http://localhost:{port}/api/stats")
    print("  ───────────────────────────────────────────────\n")

    app.run(debug=debug_mode, host="0.0.0.0", port=port)
