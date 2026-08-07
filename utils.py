import random
import string
from functools import wraps
from datetime import datetime
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        if not current_user.is_admin:
            flash("You don't have permission to access that page.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


def generate_reference(prefix):
    """Generate a unique-looking reference number like FIR-2026-4821."""
    year = datetime.utcnow().year
    rand = "".join(random.choices(string.digits, k=4))
    return f"{prefix}-{year}-{rand}"


def allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def log_activity(db, ActivityLog, user_id, action):
    try:
        entry = ActivityLog(user_id=user_id, action=action)
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()
