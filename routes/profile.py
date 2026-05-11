from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.user import User, db, ROLE_ADMIN, ROLE_SUPER_ADMIN, delete_user
from werkzeug.utils import secure_filename
import os
import logging
from config import Config
from services.auth_service import authenticate_user
from services.email_service import send_verification_email
from utils.security import generate_code, build_expiry
from utils.validators import validate_email, validate_moroccan_phone

logger = logging.getLogger(__name__)

profile_bp = Blueprint('profile', __name__)

PROFILE_IMAGE_FOLDER = "user_uploads"
LEGACY_PROFILE_IMAGE_FOLDER = "uploads"
ALLOWED_PROFILE_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif"}


def normalize_profile_image_name(stored_value):
    if not stored_value:
        return ""

    normalized = str(stored_value).replace("\\", "/").strip().lstrip("/")

    if normalized.lower().startswith("static/"):
        normalized = normalized[7:]

    return os.path.basename(normalized)


def build_profile_image_url(stored_value):
    image_name = normalize_profile_image_name(stored_value)
    if not image_name:
        return None

    current_path = os.path.join(Config.UPLOAD_DIR, image_name)
    if os.path.exists(current_path):
        return url_for("static", filename=f"{PROFILE_IMAGE_FOLDER}/{image_name}")

    legacy_dir = os.path.join(os.path.dirname(Config.UPLOAD_DIR), LEGACY_PROFILE_IMAGE_FOLDER)
    legacy_path = os.path.join(legacy_dir, image_name)
    if os.path.exists(legacy_path):
        return url_for("static", filename=f"{LEGACY_PROFILE_IMAGE_FOLDER}/{image_name}")

    return None


@profile_bp.route("/profile", methods=["GET", "POST"])
def view_profile():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    username = session["user"]
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        profile_pic = request.files.get("profile_picture")

        if profile_pic and profile_pic.filename:
            ext = os.path.splitext(profile_pic.filename)[1].lower()

            if ext not in ALLOWED_PROFILE_IMAGE_EXTENSIONS:
                flash("Only PNG/JPG/GIF allowed.", "danger")
                return redirect(url_for("profile.view_profile"))

            filename = secure_filename(f"profile_{username}{ext}")
            uploads_dir = Config.UPLOAD_DIR
            os.makedirs(uploads_dir, exist_ok=True)

            filepath = os.path.join(uploads_dir, filename)
            profile_pic.save(filepath)

            # Store only the filename so the image remains portable across machines.
            user.profile_picture = filename

            logger.info("[PROFILE] Image saved: %s", filepath)
            flash("Profile image updated.", "success")

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name

        db.session.commit()

        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile.view_profile"))

    profile_image_url = build_profile_image_url(user.profile_picture)

    return render_template(
        "profile.html",
        user=user,
        username=username,
        name=session.get("name"),
        role=user.role,
        profile_image_url=profile_image_url
    )


@profile_bp.route("/delete-account", methods=["POST"])
def delete_account():
    """
    Self-service account deletion for normal users only.
    
    Security checks:
    1. User must be logged in
    2. Can only delete own account (session username matches)
    3. Blocks admin and super_admin from self-deletion
    4. POST only to prevent accidental deletion via GET
    5. Cascading delete handles related calculations
    """
    # Check if user is logged in
    if "user" not in session:
        flash("You must be logged in to delete your account.", "danger")
        return redirect(url_for("auth.login"))

    session_username = session.get("user")
    
    # Get current user from database
    user = User.query.filter_by(username=session_username).first()
    
    if not user:
        flash("User not found.", "danger")
        session.clear()
        return redirect(url_for("auth.login"))
    
    # Security: Block admin and super_admin from self-deletion
    if user.role in {ROLE_ADMIN, ROLE_SUPER_ADMIN}:
        logger.warning(
            "[ACCOUNT_DELETE] Blocked deletion attempt for %s with role=%s",
            session_username,
            user.role
        )
        flash(
            "Admin and super admin accounts cannot be deleted through profile settings. "
            "Contact system administrator for account removal.",
            "danger"
        )
        return redirect(url_for("profile.view_profile"))
    
    # Delete the user (cascades to calculations via foreign key)
    username_to_delete = user.username
    if delete_user(username_to_delete):
        logger.info("[ACCOUNT_DELETE] User account deleted: %s", username_to_delete)
        
        # Clear session and logout
        session.clear()
        
        flash(
            "Your account has been successfully deleted. All associated data has been removed.",
            "success"
        )
        return redirect(url_for("main.home"))
    else:
        logger.error("[ACCOUNT_DELETE] Failed to delete user: %s", session_username)
        flash("Failed to delete account. Please try again or contact support.", "danger")
        return redirect(url_for("profile.view_profile"))


@profile_bp.route("/change-email", methods=["POST"])
def change_email():
    """
    Change user email address with validation and re-verification.
    """
    if "user" not in session:
        flash("You must be logged in to change your email.", "danger")
        return redirect(url_for("auth.login"))

    session_username = session.get("user")
    user = User.query.filter_by(username=session_username).first()

    if not user:
        flash("User not found.", "danger")
        session.clear()
        return redirect(url_for("auth.login"))

    current_email = request.form.get("current_email", "").strip()
    new_email = request.form.get("new_email", "").strip()
    confirm_new_email = request.form.get("confirm_new_email", "").strip()
    password = request.form.get("password", "")

    # Validate current email matches
    if current_email != user.email:
        flash("Current email does not match your account email.", "danger")
        return redirect(url_for("profile.view_profile"))

    # Validate new email
    email_valid, email_error = validate_email(new_email)
    if not email_valid:
        flash(email_error, "danger")
        return redirect(url_for("profile.view_profile"))

    # Check if new email matches confirm
    if new_email != confirm_new_email:
        flash("New email and confirmation do not match.", "danger")
        return redirect(url_for("profile.view_profile"))

    # Check if email is already taken
    existing_user = User.query.filter_by(email=new_email).first()
    if existing_user and existing_user.id != user.id:
        flash("This email address is already registered.", "danger")
        return redirect(url_for("profile.view_profile"))

    # Verify password
    _, _, auth_error, _ = authenticate_user(user.username, password)
    if auth_error:
        flash("Incorrect password. Please try again.", "danger")
        return redirect(url_for("profile.view_profile"))

    # Update email and reset verification
    user.email = new_email
    user.verified = False
    user.verification_code = generate_code()
    user.verification_expiry = build_expiry()

    db.session.commit()

    # Send verification email to new address
    try:
        send_verification_email(new_email, user.first_name, user.verification_code)
        logger.info("Verification email sent to new email: %s", new_email)
    except Exception as e:
        logger.exception("Failed to send verification email to %s", new_email)
        flash("Email address updated, but failed to send verification email. Please contact support.", "warning")
        return redirect(url_for("profile.view_profile"))

    flash("Email address updated successfully. Please check your new email for a verification code.", "success")
    return redirect(url_for("auth.verify", email=new_email))


@profile_bp.route("/change-phone", methods=["POST"])
def change_phone():
    """
    Change user phone number with validation.
    """
    if "user" not in session:
        flash("You must be logged in to change your phone.", "danger")
        return redirect(url_for("auth.login"))

    session_username = session.get("user")
    user = User.query.filter_by(username=session_username).first()

    if not user:
        flash("User not found.", "danger")
        session.clear()
        return redirect(url_for("auth.login"))

    current_phone = request.form.get("current_phone", "").strip()
    new_phone = request.form.get("new_phone", "").strip()
    confirm_new_phone = request.form.get("confirm_new_phone", "").strip()
    password = request.form.get("password", "")

    # Validate current phone matches
    if current_phone != (user.phone or ""):
        flash("Current phone does not match your account phone.", "danger")
        return redirect(url_for("profile.view_profile"))

    # Validate new phone
    validated_phone, phone_error = validate_moroccan_phone(new_phone)
    if phone_error:
        flash(phone_error, "danger")
        return redirect(url_for("profile.view_profile"))

    # Check if new phone matches confirm
    if new_phone != confirm_new_phone:
        flash("New phone and confirmation do not match.", "danger")
        return redirect(url_for("profile.view_profile"))

    # Check if phone is already taken (if not empty)
    if validated_phone:
        existing_user = User.query.filter_by(phone=validated_phone).first()
        if existing_user and existing_user.id != user.id:
            flash("This phone number is already registered.", "danger")
            return redirect(url_for("profile.view_profile"))

    # Verify password
    _, _, auth_error, _ = authenticate_user(user.username, password)
    if auth_error:
        flash("Incorrect password. Please try again.", "danger")
        return redirect(url_for("profile.view_profile"))

    # Update phone
    user.phone = validated_phone

    db.session.commit()

    flash("Phone number updated successfully.", "success")
    return redirect(url_for("profile.view_profile"))
