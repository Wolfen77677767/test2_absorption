# utils/security.py

from datetime import datetime, timedelta
import random
import re
from werkzeug.security import generate_password_hash, check_password_hash


# ==================================================
# PASSWORD HASHING
# ==================================================

def hash_password(password):
    """
    Convert plain password to secure hash
    """
    return generate_password_hash(password)


def verify_password(hashed_password, password):
    """
    Verify password.

    Supports:
    1) New hashed passwords
    2) Old plain text passwords
    """

    if not hashed_password:
        return False

    try:
        return check_password_hash(hashed_password, password)

    except ValueError:
        # Old plain text password support
        return hashed_password == password

    except Exception:
        return False


# ==================================================
# PASSWORD VALIDATION
# ==================================================

def password_valid(password):
    """
    Strong password rules:
    - Minimum 8 chars
    - 1 uppercase
    - 1 lowercase
    - 1 digit
    """

    if not password:
        return False

    if len(password) < 8:
        return False

    if not re.search(r"[A-Z]", password):
        return False

    if not re.search(r"[a-z]", password):
        return False

    if not re.search(r"\d", password):
        return False

    return True


# ==================================================
# VERIFICATION / RESET CODE
# ==================================================

def generate_code():
    """
    Generate 6 digit code
    """
    return str(random.randint(100000, 999999))


# ==================================================
# EXPIRY TIME
# ==================================================

def build_expiry(minutes=10):
    """
    Return datetime expiry object
    """
    return datetime.utcnow() + timedelta(minutes=minutes)


def is_code_expired(expiry):
    """
    Supports:
    - datetime object
    - string
    - None
    """

    if expiry is None:
        return True

    if isinstance(expiry, str):
        try:
            expiry = datetime.fromisoformat(expiry)
        except:
            return True

    if not isinstance(expiry, datetime):
        return True

    return datetime.utcnow() > expiry