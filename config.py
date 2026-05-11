import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is required and must point to a PostgreSQL database, "
        "e.g. postgresql://postgres:YOUR_PASSWORD@localhost:5432/projet_collect"
    )

if not DATABASE_URL.lower().startswith(("postgresql://", "postgres://", "postgresql+")):
    raise ValueError("DATABASE_URL must point to PostgreSQL, for example postgresql://user:pass@host:port/dbname")

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-1234")
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com").strip()
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = str(os.environ.get("MAIL_USE_TLS", "true")).strip().lower() in {"1", "true", "yes", "on"}
    MAIL_USE_SSL = str(os.environ.get("MAIL_USE_SSL", "false")).strip().lower() in {"1", "true", "yes", "on"}
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "").strip() or None
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "").strip() or None
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "").strip() or MAIL_USERNAME

    UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "user_uploads")
    CODE_EXPIRY_MINUTES = 15

    PAYPAL_MODE = os.environ.get("PAYPAL_MODE", "sandbox").strip()
    PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "").strip()
    PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "").strip()
    PAYPAL_PLAN_ID_MONTHLY = os.environ.get("PAYPAL_PLAN_ID_MONTHLY", "").strip()
    PAYPAL_PLAN_ID_YEARLY = os.environ.get("PAYPAL_PLAN_ID_YEARLY", "").strip()
    PAYPAL_RETURN_URL = os.environ.get("PAYPAL_RETURN_URL", "").strip()
    PAYPAL_CANCEL_URL = os.environ.get("PAYPAL_CANCEL_URL", "").strip()

    # SQLAlchemy Database Configuration
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
