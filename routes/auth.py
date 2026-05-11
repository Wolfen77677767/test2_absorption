from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from services.auth_service import (
    UNVERIFIED_ACCOUNT_MESSAGE,
    register_user,
    authenticate_user,
    verify_user_account,
    resend_verification_code,
    initiate_password_reset,
    reset_user_password
)
from utils.validators import MOROCCAN_PHONE_ERROR_MESSAGE, normalize_email, validate_moroccan_phone
from utils.security import password_valid
from models.user import find_user_by_identifier
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


def _resolve_verification_email(identifier_or_email):
    normalized_value = normalize_email(identifier_or_email or "")

    if not normalized_value:
        return ""

    _, user = find_user_by_identifier(normalized_value)
    return user.email if user else normalized_value


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        username = request.form.get("username", "").strip().lower()
        email = normalize_email(request.form.get("email", ""))
        confirm_email = normalize_email(request.form.get("confirm_email", ""))
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", request.form.get("confirm", ""))
        raw_phone = request.form.get("phone", "")
        phone, phone_error = validate_moroccan_phone(raw_phone)

        if not first_name or not last_name or not username or not email or not confirm_email or not password or not confirm_password:
            flash("All fields are required.", "danger")
            return render_template("signup.html")

        if email != confirm_email:
            flash("Email and confirm email must match.", "danger")
            return render_template("signup.html")

        if password != confirm_password:
            flash("Password and confirm password must match.", "danger")
            return render_template("signup.html")

        if not password_valid(password):
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("signup.html")

        if phone_error:
            return render_template("signup.html", phone_error=phone_error)

        success, message = register_user(
            first_name,
            last_name,
            username,
            email,
            password,
            phone
        )

        if not success:
            if message == MOROCCAN_PHONE_ERROR_MESSAGE:
                return render_template("signup.html", phone_error=message)

            flash(message, "danger")
            return render_template("signup.html")

        flash(message, "success")
        return redirect(url_for("auth.verify", email=email))

    return render_template("signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = (
            request.form.get("username")
            or request.form.get("email")
            or request.form.get("identifier", "")
        ).strip().lower()
        password = request.form.get("password", "")

        username, name, error, user = authenticate_user(identifier, password)
        if error:
            if error == UNVERIFIED_ACCOUNT_MESSAGE and user and not user.is_verified:
                resend_success, resend_message = resend_verification_code(user.email)

                if resend_success:
                    flash("Your account is not verified. We sent you a verification code.", "warning")
                else:
                    flash(f"Your account is not verified. {resend_message}", "danger")

                return redirect(url_for("auth.verify", email=user.email))

            flash(error, "danger")
            return render_template(
                "login.html",
                show_verification_link=bool(identifier),
                verification_target=_resolve_verification_email(identifier),
            )

        session.clear()
        session["user"] = username
        session["name"] = name

        if user:
            session["role"] = user.role
            session["verified"] = user.verified
            logger.info(f"User {username} logged in with role: {user.role}")

        user_role = user.role if user else "user"

        if user_role == "admin":
            return redirect(url_for("admin.admin_dashboard"))
        else:
            return redirect(url_for("main.user_dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/verify", methods=["GET", "POST"])
def verify():
    email = _resolve_verification_email(request.args.get("email", ""))

    if request.method == "POST":
        submitted_identifier = request.form.get("email") or request.args.get("email", "")
        email = _resolve_verification_email(submitted_identifier)
        verification_code = request.form.get("verification_code", "").strip()

        if not submitted_identifier or not verification_code:
            flash("Email and verification code are required.", "danger")
            return render_template("verify.html", email=email)

        success, message = verify_user_account(submitted_identifier, verification_code)
        if not success:
            flash(message, "danger")
            return render_template("verify.html", email=email)

        flash(message, "success")
        return redirect(url_for("auth.login"))

    return render_template("verify.html", email=email)


@auth_bp.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    email = _resolve_verification_email(request.args.get("email", ""))

    if request.method == "POST":
        submitted_identifier = request.form.get("email") or request.args.get("email", "")
        email = _resolve_verification_email(submitted_identifier)

        if not submitted_identifier:
            flash("Email is required.", "danger")
            return render_template("resend_verification.html", email=email)

        success, message = resend_verification_code(submitted_identifier)
        flash(message, "success" if success else "info")
        return render_template("resend_verification.html", email=email)

    return render_template("resend_verification.html", email=email)


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    email = normalize_email(request.args.get("email", ""))

    if request.method == "POST":
        email = normalize_email(request.form.get("email", ""))

        if not email:
            flash("Email is required.", "danger")
            return render_template("forgot_password.html", email=email)

        message = initiate_password_reset(email)
        flash(message, "info")
        return render_template("forgot_password.html", email=email)

    return render_template("forgot_password.html", email=email)


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    email = normalize_email(request.args.get("email", ""))

    if request.method == "POST":
        email = normalize_email(request.form.get("email", ""))
        reset_code = request.form.get("reset_code", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_new_password = request.form.get("confirm_new_password", "")

        if not email or not reset_code or not new_password or not confirm_new_password:
            flash("All fields are required.", "danger")
            return render_template("reset_password.html", email=email)

        if new_password != confirm_new_password:
            flash("New password and confirm new password must match.", "danger")
            return render_template("reset_password.html", email=email)

        success, message = reset_user_password(email, reset_code, new_password)
        if not success:
            flash(message, "danger")
            return render_template("reset_password.html", email=email)

        flash(message, "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", email=email)
