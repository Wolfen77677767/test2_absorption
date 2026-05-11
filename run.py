"""
Flask application factory
"""

import logging
import os

from dotenv import load_dotenv
from flask import Flask
from flask_bcrypt import Bcrypt
from sqlalchemy import text

from config import Config
from models.user import db, ensure_super_admin
from routes.admin import admin_bp
from routes.api import api_bp
from routes.auth import auth_bp
from routes.chatbot import chatbot_bp
from routes.main import main_bp
from routes.profile import profile_bp
from routes.settings import settings_bp
from routes.unit_operations import unit_ops_bp
from services.email_service import mail

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not os.getenv("TWILIO_ACCOUNT_SID"):
    logger.warning("TWILIO_ACCOUNT_SID not found in .env")
else:
    logger.info("Twilio environment loaded")


def ensure_user_auth_columns():
    """Safely add missing auth columns to users table for PostgreSQL."""
    required_columns = {
        "failed_attempts": "INTEGER DEFAULT 0",
        "lock_until": "TIMESTAMP",
        "lock_level": "INTEGER DEFAULT 0",
        "is_banned": "BOOLEAN DEFAULT FALSE",
        "banned_by_id": "INTEGER",
        "role_changed_by_id": "INTEGER",
    }

    try:
        result = db.session.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'users' AND table_schema = current_schema()"
            )
        )
        existing_columns = {row[0] for row in result.fetchall()}

        for col_name, col_def in required_columns.items():
            if col_name not in existing_columns:
                db.session.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
                logger.info("Added column %s to users table", col_name)

        db.session.execute(text("UPDATE users SET failed_attempts = 0 WHERE failed_attempts IS NULL"))
        db.session.execute(text("UPDATE users SET lock_level = 0 WHERE lock_level IS NULL"))
        db.session.execute(text("UPDATE users SET is_banned = FALSE WHERE is_banned IS NULL"))

        db.session.commit()
        logger.info("User auth columns verified/added and NULL values normalized")

    except Exception as e:
        logger.error("Failed to add auth columns: %s", e)
        db.session.rollback()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    Bcrypt(app)
    mail.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(unit_ops_bp)

    with app.app_context():
        db.create_all()
        ensure_user_auth_columns()
        ensure_super_admin()
        logger.info("Database tables created/verified")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5050, debug=True)