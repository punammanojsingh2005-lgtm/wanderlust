"""
Wander — SQLite Database Initialization & Helpers
"""
import sqlite3
import bcrypt
from config import Config


def get_db():
    """Return a new database connection with row_factory set."""
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create all tables if they don't exist and seed the admin user."""
    conn = get_db()
    c = conn.cursor()

    # ── Users ──────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            password_hash TEXT  NOT NULL,
            is_admin    INTEGER DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Bookings ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id           INTEGER NOT NULL,
            destination_id    INTEGER NOT NULL,
            destination_name  TEXT    NOT NULL,
            destination_image TEXT,
            destination_country TEXT,
            travel_date       TEXT    NOT NULL,
            num_guests        INTEGER DEFAULT 1,
            total_amount      REAL,
            status            TEXT    DEFAULT 'pending',
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Payments ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id        INTEGER,
            user_id           INTEGER NOT NULL,
            stripe_payment_id TEXT,
            amount            REAL    NOT NULL,
            currency          TEXT    DEFAULT 'usd',
            status            TEXT    DEFAULT 'pending',
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings(id),
            FOREIGN KEY (user_id)    REFERENCES users(id)
        )
    """)

    # ── User Reviews ────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_reviews (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL,
            destination_id INTEGER NOT NULL,
            rating         INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            review_text    TEXT    NOT NULL,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Newsletter ──────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS newsletter (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT    UNIQUE NOT NULL,
            subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Saved Destinations ──────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS saved_destinations (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id             INTEGER NOT NULL,
            destination_id      INTEGER NOT NULL,
            destination_name    TEXT,
            destination_image   TEXT,
            destination_country TEXT,
            saved_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, destination_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Seed default admin ──────────────────────────────────────────────────
    existing_admin = c.execute(
        "SELECT id FROM users WHERE email = ?", ("admin@wander.com",)
    ).fetchone()
    if not existing_admin:
        admin_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")
        c.execute(
            "INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
            ("Admin", "admin@wander.com", admin_hash, 1),
        )

    conn.commit()
    conn.close()
    print("  ✅  Database initialised — wander.db")
