"""
Wander — Application Configuration
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "wander-luxury-secret-8f3e2b1a-dev")
    DATABASE = os.path.join(BASE_DIR, "data", "wander.db")

    # Stripe — replace with your real keys or set as env vars
    # Test cards: 4242 4242 4242 4242 (any future date, any CVC)
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "sk_test_demo")
    STRIPE_PUBLISHABLE_KEY = os.environ.get(
        "STRIPE_PUBLISHABLE_KEY", "pk_test_demo"
    )
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_demo")

    # If STRIPE_DEMO_MODE=True, payments are simulated without calling Stripe API
    STRIPE_DEMO_MODE = os.environ.get("STRIPE_DEMO_MODE", "true").lower() == "true"
