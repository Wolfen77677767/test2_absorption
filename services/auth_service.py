from datetime import datetime, timedelta
import logging

from flask import request

from models.user import (
    User, db, find_user_by_identifier, find_user_by_email,
    add_user_history, update_user_last_ip, get_users_by_ip
)
from services.email_service import (
    send_verification_email,
    send_reset_password_email
)
from utils.security import (
    hash_password,
    verify_password,
    generate_code,
    build_expiry,
    is_code_expired
)
from utils.validators import validate_moroccan_phone
from utils.whatsapp import send_otp

logger = logging.getLogger(__name__)
UNVERIFIED_ACCOUNT_MESSAGE = "Please verify your account first."


# =====================================================
# HELPERS
# =====================================================

def get_client_ip():
    if request:
        forwarded = request.headers.get("X-Forwarded-For")

        if forwarded:
            return forwarded.split(",")[0].strip()

        return request.remote_addr or "unknown"

    return "unknown"


def get_user_agent():
    if request:
        return request.headers.get("User-Agent", "unknown")[:500]

    return "unknown"


# =====================================================
# LOGIN SECURITY HELPERS
# =====================================================

def is_account_locked(user):
    """Check if the account is currently locked."""
    if user.lock_until and datetime.utcnow() < user.lock_until:
        return True, user.lock_until - datetime.utcnow()
    return False, None


def get_lock_duration(level):
    """Get lock duration in minutes based on lock level."""
    if level == 1:
        return 1
    elif level == 2:
        return 5
    elif level == 3:
        return 10
    else:
        return 10 + (level - 3) * 5


def format_remaining_time(delta):
    """Format timedelta to human-readable string."""
    total_seconds = int(delta.total_seconds())
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    if minutes > 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''} and {seconds} second{'s' if seconds != 1 else ''}"
    return f"{seconds} second{'s' if seconds != 1 else ''}"


def normalize_auth_fields(user):
    """Normalize auth fields to handle NULL values from database."""
    if user.failed_attempts is None:
        user.failed_attempts = 0
    if user.lock_level is None:
        user.lock_level = 0


def get_user_by_auth_identifier(identifier):
    """Resolve a user from either a username or an email address."""
    normalized_identifier = "" if identifier is None else str(identifier).strip().lower()

    if not normalized_identifier:
        return None

    _, user = find_user_by_identifier(normalized_identifier)
    return user


# =====================================================
# REGISTER
# =====================================================

def register_user(first_name, last_name, username, email, password, phone=None):
    phone, phone_error = validate_moroccan_phone(phone)
    if phone_error:
        return False, phone_error

    logger.info("Registering user %s with phone=%s", username, phone or "none")

    if User.query.filter_by(username=username).first():
        return False, "This username already exists."

    if User.query.filter_by(email=email).first():
        return False, "This email is already registered."

    verification_code = generate_code()
    role = "admin" if User.query.count() == 0 else "user"
    client_ip = get_client_ip()
    user_agent = get_user_agent()

    user = User(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        phone=phone,
        password=hash_password(password),
        verified=False,
        role=role,
        status="pending",
        verification_code=verification_code,
        verification_expiry=build_expiry(),
        last_ip=client_ip,
        last_user_agent=user_agent
    )

    db.session.add(user)
    db.session.commit()

    try:
        send_verification_email(email, first_name, verification_code)
        logger.info("Verification email queued for %s", email)
    except Exception:
        logger.exception("Failed to send verification email to %s", email)

    if phone:
        try:
            result = send_otp(phone, verification_code)
            logger.info("WhatsApp OTP send result for %s: %s", phone, result)
        except Exception:
            logger.exception("WhatsApp OTP failed for %s", phone)
    else:
        logger.info("No phone provided for %s; skipping WhatsApp OTP", username)

    return True, "Account created. Check your email & WhatsApp."


# =====================================================
# LOGIN
# =====================================================

def authenticate_user(identifier, password):
    username, user = find_user_by_identifier(identifier)

    client_ip = get_client_ip()
    user_agent = get_user_agent()

    if not user:
        return None, None, "Incorrect credentials.", None

    normalize_auth_fields(user)

    locked, remaining = is_account_locked(user)
    if locked:
        return None, None, f"Account is temporarily locked. Try again in {format_remaining_time(remaining)}.", None

    if not verify_password(user.password, password):
        user.failed_attempts += 1
        if user.failed_attempts >= 3:
            user.lock_level += 1
            duration_minutes = get_lock_duration(user.lock_level)
            user.lock_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
            user.failed_attempts = 0
            db.session.commit()
            return None, None, f"Too many failed attempts. Account locked for {duration_minutes} minute{'s' if duration_minutes != 1 else ''}.", None
        db.session.commit()
        return None, None, "Incorrect credentials.", None

    display_name = f"{user.first_name} {user.last_name}".strip()

    if not user.verified:
        user.failed_attempts = 0
        user.lock_until = None
        user.lock_level = 0
        db.session.commit()
        return username, display_name, UNVERIFIED_ACCOUNT_MESSAGE, user

    if user.status == "banned":
        return None, None, "Your account has been banned.", None

    if user.status == "archived":
        return None, None, "Your account is archived.", None

    user.failed_attempts = 0
    user.lock_until = None
    user.lock_level = 0
    db.session.commit()

    update_user_last_ip(username, client_ip, user_agent)

    add_user_history(
        username,
        "login",
        client_ip,
        user_agent,
        "Successful login"
    )

    return username, display_name, None, user


# =====================================================
# VERIFY ACCOUNT
# =====================================================

def verify_user_account(identifier_or_email, verification_code):
    user = get_user_by_auth_identifier(identifier_or_email)

    client_ip = get_client_ip()
    user_agent = get_user_agent()

    if not user:
        return False, "No account found."

    if user.verified:
        return False, "Account already verified. Please sign in."

    if user.verification_code != verification_code:
        add_user_history(
            user.username,
            "verification_failed",
            client_ip,
            user_agent,
            "Wrong verification code"
        )
        return False, "Invalid verification code. Please check the 6-digit code and try again."

    if is_code_expired(user.verification_expiry):
        return False, "Verification code expired. Request a new code and try again."

    user.verified = True
    user.status = "active"
    user.verification_code = None
    user.verification_expiry = None

    db.session.commit()

    add_user_history(
        user.username,
        "verification_success",
        client_ip,
        user_agent,
        "Account verified"
    )

    return True, "Account verified successfully."


# =====================================================
# RESEND CODE
# =====================================================

def resend_verification_code(email):
    user = get_user_by_auth_identifier(email)

    if not user:
        return False, "Account not found."

    if user.verified:
        return False, "Account already verified."

    new_code = generate_code()

    user.verification_code = new_code
    user.verification_expiry = build_expiry()

    db.session.commit()

    try:
        send_verification_email(user.email, user.first_name, new_code)

        if user.phone:
            send_otp(user.phone, new_code)

        return True, "New verification code sent."

    except Exception:
        logger.exception("Failed to resend verification email to %s", user.email)
        return False, "Code generated but sending failed."


# =====================================================
# PASSWORD RESET REQUEST
# =====================================================

def initiate_password_reset(email):
    _, user = find_user_by_email(email)

    if user:
        code = generate_code()

        user.reset_code = code
        user.reset_expiry = build_expiry()

        db.session.commit()

        try:
            send_reset_password_email(
                email,
                user.first_name,
                code
            )
            logger.info("Reset password email queued for %s", email)
        except Exception:
            logger.exception("Failed to send reset password email to %s", email)

    return "If this email exists, reset code sent."


# =====================================================
# RESET PASSWORD
# =====================================================

def reset_user_password(email, reset_code, new_password):
    _, user = find_user_by_email(email)

    if not user:
        return False, "Invalid email or code."

    if user.reset_code != reset_code:
        return False, "Invalid email or code."

    if is_code_expired(user.reset_expiry):
        return False, "Reset code expired."

    user.password = hash_password(new_password)
    user.reset_code = None
    user.reset_expiry = None

    db.session.commit()

    add_user_history(
        user.username,
        "password_reset",
        get_client_ip(),
        get_user_agent(),
        "Password changed"
    )

    return True, "Password reset successful."
