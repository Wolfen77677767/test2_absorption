from functools import wraps

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from models.user import (
    ROLE_ADMIN,
    ROLE_USER,
    User,
    add_user_history,
    archive_user,
    ban_user,
    change_user_role,
    delete_user,
    get_all_users_with_details,
    get_statistics,
    unarchive_user,
    unban_user,
)
from services.auth_service import resend_verification_code

admin_bp = Blueprint("admin", __name__, url_prefix="/dashboard")


def get_current_user():
    username = session.get("user")
    if not username:
        return None
    return User.query.filter_by(username=username).first()


def check_admin():
    current_user = get_current_user()
    return bool(current_user and current_user.is_admin())


def super_admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        current_user = get_current_user()
        if not current_user:
            return json_response(False, "Please log in to continue.", 401)

        if not current_user.is_super_admin():
            return json_response(False, "Only the super admin can perform this action.", 403)

        return view_func(*args, **kwargs)

    return wrapped_view


def get_client_ip():
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "unknown"


def json_response(success, message, status_code=200):
    return jsonify({"success": success, "message": message}), status_code


def get_manageability_error(actor, target):
    if not target:
        return "User not found."

    if target.username == actor.username:
        return "You cannot modify your own account."

    if target.is_super_admin():
        return "The super admin account cannot be modified."

    if not actor.is_super_admin() and target.role != ROLE_USER:
        return "Normal admins can manage regular users only."

    return None


@admin_bp.route("/admin", methods=["GET"])
def admin_dashboard():
    current_user = get_current_user()

    if not current_user:
        flash("Please log in to access the admin dashboard.", "warning")
        return redirect(url_for("auth.login"))

    if not current_user.is_admin():
        flash("Access denied.", "danger")
        return redirect(url_for("main.user_dashboard"))

    session["role"] = current_user.role

    users_list = get_all_users_with_details()
    stats = get_statistics()

    return render_template(
        "admin_dashboard.html",
        users=users_list,
        total_users=stats.get("total_users", 0),
        admin_count=stats.get("admin_count", 0),
        standard_user_count=stats.get("standard_user_count", 0),
        banned_count=stats.get("banned_count", 0),
        archived_count=stats.get("archived_count", 0),
        pending_count=stats.get("pending_count", 0),
        verified_users=stats.get("verified_users", 0),
        admin_username=current_user.username,
        current_user=current_user,
        current_is_super_admin=current_user.is_super_admin(),
    )


@admin_bp.route("/admin/ban/<username>", methods=["POST"])
def ban_user_route(username):
    current_user = get_current_user()
    if not current_user or not current_user.is_admin():
        return json_response(False, "Only admins can perform this action.", 403)

    target_user = User.query.filter_by(username=username).first()
    permission_error = get_manageability_error(current_user, target_user)
    if permission_error:
        return json_response(False, permission_error, 403 if target_user else 404)

    if target_user.is_banned:
        return json_response(False, f"User {username} is already banned.")

    if ban_user(username, banned_by=current_user):
        add_user_history(
            username,
            "admin_ban",
            get_client_ip(),
            None,
            f"Banned by admin {current_user.username}",
        )
        return json_response(True, f"User {username} has been banned.")

    return json_response(False, f"Could not ban user {username}.")


@admin_bp.route("/admin/unban/<username>", methods=["POST"])
def unban_user_route(username):
    current_user = get_current_user()
    if not current_user or not current_user.is_admin():
        return json_response(False, "Only admins can perform this action.", 403)

    target_user = User.query.filter_by(username=username).first()
    permission_error = get_manageability_error(current_user, target_user)
    if permission_error:
        return json_response(False, permission_error, 403 if target_user else 404)

    if not target_user.is_banned:
        return json_response(False, f"User {username} is not banned.")

    if unban_user(username):
        add_user_history(
            username,
            "admin_unban",
            get_client_ip(),
            None,
            f"Unbanned by admin {current_user.username}",
        )
        return json_response(True, f"User {username} has been unbanned.")

    return json_response(False, f"Could not unban user {username}.")


@admin_bp.route("/admin/promote/<username>", methods=["POST"])
@super_admin_required
def promote_user(username):
    current_user = get_current_user()
    target_user = User.query.filter_by(username=username).first()

    if not target_user:
        return json_response(False, f"User {username} not found.", 404)

    if target_user.username == current_user.username:
        return json_response(False, "You cannot promote yourself.")

    if target_user.is_super_admin():
        return json_response(False, "The super admin account cannot be modified.", 403)

    if target_user.role != ROLE_USER:
        return json_response(False, f"User {username} is already an admin.")

    if change_user_role(username, ROLE_ADMIN, changed_by=current_user):
        add_user_history(
            username,
            "admin_promote",
            get_client_ip(),
            None,
            f"Promoted to admin by {current_user.username}",
        )
        return json_response(True, f"User {username} is now an admin.")

    return json_response(False, f"Could not promote user {username}.")


@admin_bp.route("/admin/warn/<username>", methods=["POST"])
def warn_user_route(username):
    current_user = get_current_user()
    if not current_user or not current_user.is_admin():
        return json_response(False, "Only admins can perform this action.", 403)

    target_user = User.query.filter_by(username=username).first()
    permission_error = get_manageability_error(current_user, target_user)
    if permission_error:
        return json_response(False, permission_error, 403 if target_user else 404)

    add_user_history(
        username,
        "admin_warn",
        get_client_ip(),
        None,
        f"Warning issued by admin {current_user.username}",
    )
    return json_response(True, f"Warning sent to {username}.")


@admin_bp.route("/admin/resend/<username>", methods=["POST"])
def resend_verification_route(username):
    current_user = get_current_user()
    if not current_user or not current_user.is_admin():
        return json_response(False, "Only admins can perform this action.", 403)

    target_user = User.query.filter_by(username=username).first()
    permission_error = get_manageability_error(current_user, target_user)
    if permission_error:
        return json_response(False, permission_error, 403 if target_user else 404)

    success, message = resend_verification_code(target_user.email)
    if success:
        add_user_history(
            username,
            "admin_resend_verification",
            get_client_ip(),
            None,
            f"Verification code resent by admin {current_user.username}",
        )

    return json_response(success, message)


@admin_bp.route("/admin/demote/<username>", methods=["POST"])
@super_admin_required
def demote_user(username):
    current_user = get_current_user()
    target_user = User.query.filter_by(username=username).first()

    if not target_user:
        return json_response(False, f"User {username} not found.", 404)

    if target_user.username == current_user.username:
        return json_response(False, "You cannot demote yourself.")

    if target_user.is_super_admin():
        return json_response(False, "The super admin account cannot be modified.", 403)

    if target_user.role != ROLE_ADMIN:
        return json_response(False, f"User {username} is not an admin.")

    if change_user_role(username, ROLE_USER, changed_by=current_user):
        add_user_history(
            username,
            "admin_demote",
            get_client_ip(),
            None,
            f"Demoted to user by {current_user.username}",
        )
        return json_response(True, f"User {username} is now a regular user.")

    return json_response(False, f"Could not demote user {username}.")


@admin_bp.route("/admin/archive/<username>", methods=["POST"])
def archive_user_route(username):
    current_user = get_current_user()
    if not current_user or not current_user.is_admin():
        return json_response(False, "Only admins can perform this action.", 403)

    target_user = User.query.filter_by(username=username).first()
    permission_error = get_manageability_error(current_user, target_user)
    if permission_error:
        return json_response(False, permission_error, 403 if target_user else 404)

    if target_user.status == "archived":
        return json_response(False, f"User {username} is already archived.")

    if archive_user(username):
        add_user_history(
            username,
            "admin_archive",
            get_client_ip(),
            None,
            f"Archived by admin {current_user.username}",
        )
        return json_response(True, f"User {username} has been archived.")

    return json_response(False, f"Could not archive user {username}.")


@admin_bp.route("/admin/unarchive/<username>", methods=["POST"])
def unarchive_user_route(username):
    current_user = get_current_user()
    if not current_user or not current_user.is_admin():
        return json_response(False, "Only admins can perform this action.", 403)

    target_user = User.query.filter_by(username=username).first()
    permission_error = get_manageability_error(current_user, target_user)
    if permission_error:
        return json_response(False, permission_error, 403 if target_user else 404)

    if target_user.status != "archived":
        return json_response(False, f"User {username} is not archived.")

    if unarchive_user(username):
        add_user_history(
            username,
            "admin_unarchive",
            get_client_ip(),
            None,
            f"Unarchived by admin {current_user.username}",
        )
        return json_response(True, f"User {username} has been unarchived.")

    return json_response(False, f"Could not unarchive user {username}.")


@admin_bp.route("/admin/delete/<username>", methods=["POST"])
def delete_user_route(username):
    current_user = get_current_user()
    if not current_user or not current_user.is_admin():
        return json_response(False, "Only admins can perform this action.", 403)

    target_user = User.query.filter_by(username=username).first()
    permission_error = get_manageability_error(current_user, target_user)
    if permission_error:
        return json_response(False, permission_error, 403 if target_user else 404)

    if delete_user(username):
        add_user_history(
            current_user.username,
            "admin_delete",
            get_client_ip(),
            None,
            f"Permanently deleted user {username}",
        )
        return json_response(True, f"User {username} has been permanently deleted.")

    return json_response(False, f"User {username} not found.", 404)
