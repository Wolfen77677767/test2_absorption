import logging
import os
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

db = SQLAlchemy()
logger = logging.getLogger(__name__)

ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_SUPER_ADMIN = "super_admin"
VALID_ROLES = {ROLE_USER, ROLE_ADMIN, ROLE_SUPER_ADMIN}
PRIMARY_SUPER_ADMIN_EMAIL = "ammarolaya@gmail.com"


# =====================================================
# USER MODEL
# =====================================================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    # Basic info
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)

    # Profile
    profile_picture = db.Column(db.String(255), nullable=True)

    # Security
    password = db.Column(db.String(255), nullable=False)

    # Account status
    verified = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default=ROLE_USER, nullable=False)
    status = db.Column(db.String(20), default="pending")
    is_banned = db.Column(db.Boolean, default=False, nullable=False)
    banned_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    role_changed_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    banned_by = db.relationship(
        "User",
        remote_side=[id],
        foreign_keys=[banned_by_id],
        backref=db.backref("banned_users", lazy="dynamic"),
    )
    role_changed_by = db.relationship(
        "User",
        remote_side=[id],
        foreign_keys=[role_changed_by_id],
        backref=db.backref("role_changed_users", lazy="dynamic"),
    )

    # Verification
    verification_code = db.Column(db.String(10), nullable=True)
    verification_expiry = db.Column(db.DateTime, nullable=True)

    # Reset password
    reset_code = db.Column(db.String(10), nullable=True)
    reset_expiry = db.Column(db.DateTime, nullable=True)

    # Login security
    failed_attempts = db.Column(db.Integer, default=0)
    lock_until = db.Column(db.DateTime, nullable=True)
    lock_level = db.Column(db.Integer, default=0)

    # Tracking
    last_ip = db.Column(db.String(50))
    last_user_agent = db.Column(db.String(500))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"

    @property
    def is_verified(self):
        return bool(self.verified)

    @property
    def profile_image(self):
        return self.profile_picture or ""

    def is_admin(self):
        return self.role in {ROLE_ADMIN, ROLE_SUPER_ADMIN}

    def is_super_admin(self):
        return self.role == ROLE_SUPER_ADMIN

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "status": self.status,
            "is_banned": bool(self.is_banned),
            "banned_by_username": self.banned_by.username if self.banned_by else None,
            "role_changed_by_username": self.role_changed_by.username if self.role_changed_by else None,
            "profile_picture": self.profile_picture or "",
        }


# =====================================================
# IP HISTORY
# =====================================================

class IPHistory(db.Model):
    __tablename__ = "ip_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# USER HISTORY
# =====================================================

class UserHistory(db.Model):
    __tablename__ = "user_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(100))
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# SCHEMA / BOOTSTRAP HELPERS
# =====================================================

def ensure_user_table_columns():
    pass


def _build_unique_super_admin_identity(base_username, base_email):
    username = base_username
    email = base_email

    email_local, at, email_domain = base_email.partition("@")
    suffix = 0

    while User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        suffix += 1
        username = f"{base_username}_{suffix}"
        if at and email_domain:
            email = f"{email_local}+{suffix}@{email_domain}"
        else:
            email = f"{base_email}.{suffix}"

    return username, email


def _normalize_super_admin_account(user):
    changed = False

    if user.role != ROLE_SUPER_ADMIN:
        user.role = ROLE_SUPER_ADMIN
        changed = True

    return changed


def _demote_other_super_admins(primary_super_admin):
    changed = False

    other_super_admins = User.query.filter(
        User.role == ROLE_SUPER_ADMIN,
        User.id != primary_super_admin.id
    ).all()

    for other_user in other_super_admins:
        other_user.role = ROLE_ADMIN
        other_user.role_changed_by_id = primary_super_admin.id
        changed = True

    return changed, len(other_super_admins)


def ensure_super_admin():
    """
    Ensure exactly one user is the super admin.
    If the account with PRIMARY_SUPER_ADMIN_EMAIL exists, promote it and downgrade any other super admin.
    Otherwise, preserve existing super admins if present or create a bootstrap super admin only when needed.
    """
    primary_super_admin = User.query.filter(
        func.lower(User.email) == PRIMARY_SUPER_ADMIN_EMAIL.lower()
    ).first()

    if primary_super_admin:
        changed = _normalize_super_admin_account(primary_super_admin)

        if primary_super_admin.role_changed_by_id is None:
            primary_super_admin.role_changed_by_id = primary_super_admin.id
            changed = True

        other_changed, demoted_count = _demote_other_super_admins(primary_super_admin)
        changed = changed or other_changed

        if changed:
            db.session.commit()
            logger.info(
                "Promoted existing user '%s' (%s) to the only super admin and demoted %s other super admin(s)",
                primary_super_admin.username,
                PRIMARY_SUPER_ADMIN_EMAIL,
                demoted_count,
            )

        return primary_super_admin

    existing_super_admins = User.query.filter_by(role=ROLE_SUPER_ADMIN).order_by(User.id.asc()).all()

    if existing_super_admins:
        super_admin = existing_super_admins[0]
        changed = _normalize_super_admin_account(super_admin)

        if super_admin.role_changed_by_id is None:
            super_admin.role_changed_by_id = super_admin.id
            changed = True

        other_changed, demoted_count = _demote_other_super_admins(super_admin)
        changed = changed or other_changed

        if changed:
            db.session.commit()
            logger.info(
                "Primary email %s not found. Reused existing super admin '%s' and demoted %s extra super admin(s)",
                PRIMARY_SUPER_ADMIN_EMAIL,
                super_admin.username,
                demoted_count,
            )

        return super_admin

    from utils.security import hash_password

    base_username = (os.getenv("SUPER_ADMIN_USERNAME", "system_super_admin") or "system_super_admin").strip().lower()
    base_email = (os.getenv("SUPER_ADMIN_EMAIL", "system.super.admin@local") or "system.super.admin@local").strip().lower()
    password = os.getenv("SUPER_ADMIN_PASSWORD", "ChangeMe123!")
    first_name = (os.getenv("SUPER_ADMIN_FIRST_NAME", "System") or "System").strip()
    last_name = (os.getenv("SUPER_ADMIN_LAST_NAME", "Super Admin") or "Super Admin").strip()

    username, email = _build_unique_super_admin_identity(base_username, base_email)

    super_admin = User(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        password=hash_password(password),
        verified=True,
        role=ROLE_SUPER_ADMIN,
        status="active",
        is_banned=False,
        banned_by=None,
        last_ip="system",
        last_user_agent="system_bootstrap",
    )

    db.session.add(super_admin)
    db.session.flush()
    super_admin.role_changed_by_id = super_admin.id
    db.session.commit()

    logger.info("Created persistent super admin account '%s'", super_admin.username)
    return super_admin


# =====================================================
# AUTH HELPERS
# =====================================================

def find_user_by_identifier(identifier):
    user = User.query.filter(
        (User.username == identifier) |
        (User.email == identifier)
    ).first()
    return (user.username, user) if user else (None, None)


def find_user_by_email(email):
    user = User.query.filter_by(email=email).first()
    return (user.username, user) if user else (None, None)


def find_user_by_username(username):
    return User.query.filter_by(username=username).first()


def get_users_by_ip(ip):
    return User.query.filter_by(last_ip=ip).all()


def update_user_last_ip(username, ip, user_agent):
    user = User.query.filter_by(username=username).first()
    if user:
        user.last_ip = ip
        user.last_user_agent = user_agent

        ip_entry = IPHistory(
            user_id=user.id,
            ip_address=ip,
            user_agent=user_agent
        )
        db.session.add(ip_entry)

        db.session.commit()


def add_user_history(username, action, ip, user_agent, description):
    user = User.query.filter_by(username=username).first()
    if user:
        history = UserHistory(
            user_id=user.id,
            action=action,
            ip_address=ip,
            user_agent=user_agent,
            description=description
        )
        db.session.add(history)
        db.session.commit()


# =====================================================
# ADMIN FUNCTIONS
# =====================================================

def get_all_users_with_details():
    return User.query.order_by(User.created_at.asc(), User.id.asc()).all()


def get_statistics():
    return {
        "total_users": User.query.count(),
        "verified_users": User.query.filter_by(verified=True).count(),
        "unverified_users": User.query.filter_by(verified=False).count(),
        "admin_count": User.query.filter(User.role.in_([ROLE_ADMIN, ROLE_SUPER_ADMIN])).count(),
        "normal_admin_count": User.query.filter_by(role=ROLE_ADMIN).count(),
        "super_admin_count": User.query.filter_by(role=ROLE_SUPER_ADMIN).count(),
        "standard_user_count": User.query.filter_by(role=ROLE_USER).count(),
        "active_count": User.query.filter_by(status="active").count(),
        "banned_count": User.query.filter_by(is_banned=True).count(),
        "archived_count": User.query.filter_by(status="archived").count(),
        "pending_count": User.query.filter_by(status="pending").count(),
    }


def ban_user(username, banned_by=None):
    user = User.query.filter_by(username=username).first()
    if user:
        user.status = "banned"
        user.is_banned = True
        user.banned_by = banned_by
        db.session.commit()
        return True
    return False


def unban_user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        user.is_banned = False
        user.banned_by = None
        user.status = "active" if user.verified else "pending"
        db.session.commit()
        return True
    return False


def archive_user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        user.status = "archived"
        user.is_banned = False
        user.banned_by = None
        db.session.commit()
        return True
    return False


def unarchive_user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        user.status = "active" if user.verified else "pending"
        db.session.commit()
        return True
    return False


def delete_user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        User.query.filter_by(banned_by_id=user.id).update({"banned_by_id": None})
        User.query.filter_by(role_changed_by_id=user.id).update({"role_changed_by_id": None})
        db.session.delete(user)
        db.session.commit()
        return True
    return False


def change_user_role(username, role, changed_by=None):
    if role not in VALID_ROLES:
        return False

    user = User.query.filter_by(username=username).first()
    if user:
        user.role = role
        user.role_changed_by = changed_by
        db.session.commit()
        return True
    return False
