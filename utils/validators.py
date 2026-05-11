import re

MOROCCAN_PHONE_ERROR_MESSAGE = "Veuillez entrer un numéro marocain valide: +2126XXXXXXXX ou 06XXXXXXXX"

def normalize_email(email):
    return email.strip().lower()


def validate_email(email):
    if not email or not isinstance(email, str):
        return False, "Email address is required."

    email = email.strip()
    if not email:
        return False, "Email address cannot be empty."

    # Basic email regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Please enter a valid email address."

    return True, None


def validate_moroccan_phone(phone):
    raw_phone = "" if phone is None else str(phone).strip()

    if not raw_phone:
        return None, None

    cleaned_phone = re.sub(r"[\s-]+", "", raw_phone)

    if re.fullmatch(r"0[67]\d{8}", cleaned_phone):
        return f"+212{cleaned_phone[1:]}", None

    if re.fullmatch(r"\+212[67]\d{8}", cleaned_phone):
        return cleaned_phone, None

    return None, MOROCCAN_PHONE_ERROR_MESSAGE


def is_user_verified(user):
    return user.get("verified", True)


def get_display_name(user, username=None):
    first_name = user.get("first_name", "").strip()
    last_name = user.get("last_name", "").strip()
    full_name = " ".join(part for part in [first_name, last_name] if part)
    return full_name or username or user.get("username", "")
