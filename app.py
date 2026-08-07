import os
from datetime import datetime, date
from collections import Counter

from flask import (Flask, render_template, redirect, url_for, request,
                    flash, jsonify, session, abort)
from flask_login import (LoginManager, login_user, logout_user, login_required,
                          current_user)
from werkzeug.utils import secure_filename

from config import Config
from models import (db, User, Complainant, FIR, Case, Evidence, Witness,
                     InvestigationNote, ChargeSheet, CourtRecord, ActivityLog)
from utils import admin_required, generate_reference, allowed_file, log_activity

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------------------------------------------------------------------
# Context processors
# ---------------------------------------------------------------------
@app.context_processor
def inject_globals():
    return {"now": datetime.utcnow()}


# ---------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active_user:
            login_user(user, remember=remember)
            log_activity(db, ActivityLog, user.id, f"{user.name} logged in")
            flash(f"Welcome back, {user.name}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard"))
        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    log_activity(db, ActivityLog, current_user.id, f"{current_user.name} logged out")
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    total_firs = FIR.query.count()
    active_cases = Case.query.filter(Case.status != "Closed").count()
    closed_cases = Case.query.filter_by(status="Closed").count()
    pending_court = CourtRecord.query.filter(CourtRecord.court_status != "Judgment").count()

    if current_user.is_admin:
        recent_firs = FIR.query.order_by(FIR.date_filed.desc()).limit(6).all()
    else:
        recent_firs = (FIR.query.join(Case).filter(Case.officer_id == current_user.id)
                        .order_by(FIR.date_filed.desc()).limit(6).all())

    status_counts = dict(Counter([c.status for c in Case.query.all()]))

    crime_type_counts = dict(Counter([f.crime_type for f in FIR.query.all()]))

    recent_activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(8).all()

    return render_template(
        "dashboard.html",
        total_firs=total_firs,
        active_cases=active_cases,
        closed_cases=closed_cases,
        pending_court=pending_court,
        recent_firs=recent_firs,
        status_counts=status_counts,
        crime_type_counts=crime_type_counts,
        recent_activity=recent_activity,
    )


@app.route("/api/dashboard-stats")
@login_required
def api_dashboard_stats():
    # Monthly FIR trend for the last 6 months
    firs = FIR.query.all()
    month_labels = []
    month_counts = []
    today = date.today()
    buckets = {}
    for i in range(5, -1, -1):
        m = (today.month - i - 1) % 12 + 1
        y = today.year + ((today.month - i - 1) // 12)
        key = f"{y}-{m:02d}"
        buckets[key] = 0

    for f in firs:
        key = f.date_filed.strftime("%Y-%m") if f.date_filed else None
        if key in buckets:
            buckets[key] += 1

    for key in buckets:
        y, m = key.split("-")
        month_labels.append(datetime(int(y), int(m), 1).strftime("%b %Y"))
        month_counts.append(buckets[key])

    status_counts = Counter([c.status for c in Case.query.all()])

    return jsonify({
        "trend_labels": month_labels,
        "trend_counts": month_counts,
        "status_labels": list(status_counts.keys()),
        "status_counts": list(status_counts.values()),
    })


# ---------------------------------------------------------------------
# FIR Management
# ---------------------------------------------------------------------
@app.route("/firs")
@login_required
def fir_list():
    query = FIR.query
    search = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    if search:
        query = query.filter(
            (FIR.fir_number.ilike(f"%{search}%")) |
            (FIR.crime_type.ilike(f"%{search}%")) |
            (FIR.location.ilike(f"%{search}%"))
        )
    if status:
        query = query.filter_by(status=status)
    firs = query.order_by(FIR.date_filed.desc()).all()
    return render_template("fir_list.html", firs=firs, search=search, status=status)


@app.route("/firs/new", methods=["GET", "POST"])
@login_required
def fir_new():
    if request.method == "POST":
        try:
            complainant = Complainant(
                name=request.form["complainant_name"],
                phone=request.form["complainant_phone"],
                email=request.form.get("complainant_email"),
                address=request.form.get("complainant_address"),
                gender=request.form.get("complainant_gender"),
            )
            db.session.add(complainant)
            db.session.flush()

            fir = FIR(
                fir_number=generate_reference("FIR"),
                crime_type=request.form["crime_type"],
                location=request.form["location"],
                date_of_incident=datetime.strptime(request.form["date_of_incident"], "%Y-%m-%d").date(),
                description=request.form["description"],
                complainant_id=complainant.id,
                filed_by_id=current_user.id,
            )
            db.session.add(fir)
            db.session.commit()
            log_activity(db, ActivityLog, current_user.id, f"Registered FIR {fir.fir_number}")
            flash(f"FIR {fir.fir_number} registered successfully.", "success")
            return redirect(url_for("fir_detail", fir_id=fir.id))
        except Exception as exc:
            db.session.rollback()
            flash(f"Error registering FIR: {exc}", "danger")

    return render_template("fir_form.html", fir=None, complainant=None)


@app.route("/firs/<int:fir_id>")
@login_required
def fir_detail(fir_id):
    fir = db.session.get(FIR, fir_id) or abort(404)
    officers = User.query.filter_by(role="officer", is_active_user=True).all()
    return render_template("fir_detail.html", fir=fir, officers=officers)


@app.route("/firs/<int:fir_id>/edit", methods=["GET", "POST"])
@login_required
def fir_edit(fir_id):
    fir = db.session.get(FIR, fir_id) or abort(404)
    if request.method == "POST":
        try:
            fir.crime_type = request.form["crime_type"]
            fir.location = request.form["location"]
            fir.date_of_incident = datetime.strptime(request.form["date_of_incident"], "%Y-%m-%d").date()
            fir.description = request.form["description"]
            fir.complainant.name = request.form["complainant_name"]
            fir.complainant.phone = request.form["complainant_phone"]
            fir.complainant.email = request.form.get("complainant_email")
            fir.complainant.address = request.form.get("complainant_address")
            db.session.commit()
            flash(f"FIR {fir.fir_number} updated.", "success")
            return redirect(url_for("fir_detail", fir_id=fir.id))
        except Exception as exc:
            db.session.rollback()
            flash(f"Error updating FIR: {exc}", "danger")

    return render_template("fir_form.html", fir=fir, complainant=fir.complainant)


@app.route("/firs/<int:fir_id>/create-case", methods=["POST"])
@login_required
def fir_create_case(fir_id):
    fir = db.session.get(FIR, fir_id) or abort(404)
    if fir.case:
        flash("A case already exists for this FIR.", "warning")
        return redirect(url_for("fir_detail", fir_id=fir.id))

    officer_id = request.form.get("officer_id") or None
    case = Case(
        case_number=generate_reference("CASE"),
        fir_id=fir.id,
        officer_id=int(officer_id) if officer_id else None,
        priority=request.form.get("priority", "Medium"),
        description=fir.description,
        status="Investigating" if officer_id else "Open",
    )
    fir.status = "Under Investigation" if officer_id else "Registered"
    db.session.add(case)
    db.session.commit()
    log_activity(db, ActivityLog, current_user.id, f"Created case {case.case_number} from {fir.fir_number}")
    flash(f"Case {case.case_number} created.", "success")
    return redirect(url_for("case_detail", case_id=case.id))


@app.route("/firs/<int:fir_id>/delete", methods=["POST"])
@login_required
@admin_required
def fir_delete(fir_id):
    fir = db.session.get(FIR, fir_id) or abort(404)
    number = fir.fir_number
    db.session.delete(fir)
    db.session.commit()
    flash(f"FIR {number} deleted.", "info")
    return redirect(url_for("fir_list"))


# ---------------------------------------------------------------------
# Case Management
# ---------------------------------------------------------------------
@app.route("/cases")
@login_required
def case_list():
    query = Case.query
    if not current_user.is_admin:
        query = query.filter_by(officer_id=current_user.id)

    status = request.args.get("status", "")
    if status:
        query = query.filter_by(status=status)

    cases = query.order_by(Case.created_at.desc()).all()
    return render_template("case_list.html", cases=cases, status=status)


@app.route("/cases/<int:case_id>")
@login_required
def case_detail(case_id):
    case = db.session.get(Case, case_id) or abort(404)
    if not current_user.is_admin and case.officer_id != current_user.id:
        flash("You are not assigned to this case.", "danger")
        return redirect(url_for("case_list"))
    officers = User.query.filter_by(role="officer", is_active_user=True).all()
    return render_template("case_detail.html", case=case, officers=officers, today=date.today())


@app.route("/cases/<int:case_id>/assign", methods=["POST"])
@login_required
@admin_required
def case_assign(case_id):
    case = db.session.get(Case, case_id) or abort(404)
    officer_id = request.form.get("officer_id")
    case.officer_id = int(officer_id) if officer_id else None
    if case.status == "Open" and officer_id:
        case.status = "Investigating"
        case.fir.status = "Under Investigation"
    db.session.commit()
    flash("Case assignment updated.", "success")
    return redirect(url_for("case_detail", case_id=case.id))


@app.route("/cases/<int:case_id>/status", methods=["POST"])
@login_required
def case_update_status(case_id):
    case = db.session.get(Case, case_id) or abort(404)
    new_status = request.form.get("status")
    if new_status in {"Open", "Investigating", "Closed"}:
        case.status = new_status
        if new_status == "Closed":
            case.closed_at = datetime.utcnow()
            case.fir.status = "Closed"
        db.session.commit()
        flash("Case status updated.", "success")
    return redirect(url_for("case_detail", case_id=case.id))


@app.route("/cases/<int:case_id>/note/add", methods=["POST"])
@login_required
def case_add_note(case_id):
    case = db.session.get(Case, case_id) or abort(404)
    note = InvestigationNote(case_id=case.id, note=request.form["note"], created_by_id=current_user.id)
    db.session.add(note)
    db.session.commit()
    flash("Investigation note added.", "success")
    return redirect(url_for("case_detail", case_id=case.id))


@app.route("/cases/<int:case_id>/witness/add", methods=["POST"])
@login_required
def case_add_witness(case_id):
    case = db.session.get(Case, case_id) or abort(404)
    witness = Witness(
        case_id=case.id,
        name=request.form["name"],
        phone=request.form.get("phone"),
        statement=request.form["statement"],
    )
    db.session.add(witness)
    db.session.commit()
    flash("Witness statement recorded.", "success")
    return redirect(url_for("case_detail", case_id=case.id))


@app.route("/cases/<int:case_id>/evidence/add", methods=["POST"])
@login_required
def case_add_evidence(case_id):
    case = db.session.get(Case, case_id) or abort(404)
    file_path = None
    file = request.files.get("file")
    if file and file.filename and allowed_file(file.filename, app.config["ALLOWED_EXTENSIONS"]):
        filename = secure_filename(f"{case.case_number}_{file.filename}")
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        file_path = filename
    elif file and file.filename:
        flash("File type not allowed.", "warning")

    evidence = Evidence(
        case_id=case.id,
        title=request.form["title"],
        description=request.form.get("description"),
        file_path=file_path,
        uploaded_by_id=current_user.id,
    )
    db.session.add(evidence)
    db.session.commit()
    flash("Evidence uploaded.", "success")
    return redirect(url_for("case_detail", case_id=case.id))


@app.route("/cases/<int:case_id>/charge-sheet/add", methods=["POST"])
@login_required
def case_add_charge_sheet(case_id):
    case = db.session.get(Case, case_id) or abort(404)
    file_path = None
    file = request.files.get("file")
    if file and file.filename and allowed_file(file.filename, app.config["ALLOWED_EXTENSIONS"]):
        filename = secure_filename(f"{case.case_number}_chargesheet_{file.filename}")
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        file_path = filename

    if case.charge_sheet:
        case.charge_sheet.summary = request.form.get("summary")
        if file_path:
            case.charge_sheet.file_path = file_path
    else:
        cs = ChargeSheet(case_id=case.id, summary=request.form.get("summary"), file_path=file_path)
        db.session.add(cs)

    case.fir.status = "Charge Sheet Filed"
    db.session.commit()
    flash("Charge sheet filed.", "success")
    return redirect(url_for("case_detail", case_id=case.id))


@app.route("/cases/<int:case_id>/court/add", methods=["POST"])
@login_required
def case_add_court_record(case_id):
    case = db.session.get(Case, case_id) or abort(404)
    record = CourtRecord(
        case_id=case.id,
        hearing_date=datetime.strptime(request.form["hearing_date"], "%Y-%m-%d").date(),
        court_status=request.form.get("court_status", "Scheduled"),
        judge_name=request.form.get("judge_name"),
        remarks=request.form.get("remarks"),
        judgment=request.form.get("judgment"),
    )
    db.session.add(record)
    case.fir.status = "In Court"
    db.session.commit()
    flash("Court record added.", "success")
    return redirect(url_for("case_detail", case_id=case.id))


# ---------------------------------------------------------------------
# Reports & Analytics
# ---------------------------------------------------------------------
@app.route("/reports")
@login_required
def reports():
    total_firs = FIR.query.count()
    total_cases = Case.query.count()
    closed_cases = Case.query.filter_by(status="Closed").count()
    open_cases = Case.query.filter(Case.status != "Closed").count()

    crime_type_counts = dict(Counter([f.crime_type for f in FIR.query.all()]))
    status_counts = dict(Counter([c.status for c in Case.query.all()]))
    priority_counts = dict(Counter([c.priority for c in Case.query.all()]))

    officer_load = Counter()
    for c in Case.query.filter(Case.officer_id.isnot(None)).all():
        officer_load[c.officer.name] += 1

    clearance_rate = round((closed_cases / total_cases * 100), 1) if total_cases else 0

    return render_template(
        "reports.html",
        total_firs=total_firs,
        total_cases=total_cases,
        closed_cases=closed_cases,
        open_cases=open_cases,
        crime_type_counts=crime_type_counts,
        status_counts=status_counts,
        priority_counts=priority_counts,
        officer_load=dict(officer_load),
        clearance_rate=clearance_rate,
    )


# ---------------------------------------------------------------------
# User Management (Admin only)
# ---------------------------------------------------------------------
@app.route("/users")
@login_required
@admin_required
def user_list():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("user_list.html", users=users)


@app.route("/users/new", methods=["GET", "POST"])
@login_required
@admin_required
def user_new():
    if request.method == "POST":
        if User.query.filter_by(username=request.form["username"]).first():
            flash("Username already exists.", "danger")
            return render_template("user_form.html", user=None)
        user = User(
            name=request.form["name"],
            username=request.form["username"],
            email=request.form.get("email"),
            role=request.form["role"],
            badge_number=request.form.get("badge_number") or None,
            phone=request.form.get("phone"),
        )
        user.set_password(request.form["password"])
        db.session.add(user)
        db.session.commit()
        flash(f"User {user.name} created.", "success")
        return redirect(url_for("user_list"))
    return render_template("user_form.html", user=None)


@app.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def user_edit(user_id):
    user = db.session.get(User, user_id) or abort(404)
    if request.method == "POST":
        user.name = request.form["name"]
        user.email = request.form.get("email")
        user.role = request.form["role"]
        user.badge_number = request.form.get("badge_number") or None
        user.phone = request.form.get("phone")
        user.is_active_user = bool(request.form.get("is_active_user"))
        if request.form.get("password"):
            user.set_password(request.form["password"])
        db.session.commit()
        flash(f"User {user.name} updated.", "success")
        return redirect(url_for("user_list"))
    return render_template("user_form.html", user=user)


@app.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def user_delete(user_id):
    if user_id == current_user.id:
        flash("You can't delete your own account.", "danger")
        return redirect(url_for("user_list"))
    user = db.session.get(User, user_id) or abort(404)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "info")
    return redirect(url_for("user_list"))


# ---------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        if not current_user.check_password(current_password):
            flash("Current password is incorrect.", "danger")
        elif len(new_password or "") < 6:
            flash("New password must be at least 6 characters.", "warning")
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash("Password updated successfully.", "success")
    return render_template("settings.html")


# ---------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403


# ---------------------------------------------------------------------
# CLI: initialize database with seed data
# ---------------------------------------------------------------------
@app.cli.command("init-db")
def init_db():
    """Create tables and seed an initial admin + demo data."""
    db.create_all()

    if not User.query.filter_by(username="admin").first():
        admin = User(name="System Admin", username="admin", email="admin@cms.gov.in",
                     role="admin", badge_number="ADM-001")
        admin.set_password("admin123")
        db.session.add(admin)

    if not User.query.filter_by(username="officer1").first():
        officer = User(name="Officer Ravi Kumar", username="officer1", email="ravi@cms.gov.in",
                        role="officer", badge_number="PO-1042", phone="9876543210")
        officer.set_password("officer123")
        db.session.add(officer)

    db.session.commit()
    print("Database initialized.")
    print("Admin login    -> username: admin     password: admin123")
    print("Officer login  -> username: officer1   password: officer123")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            admin = User(name="System Admin", username="admin", email="admin@cms.gov.in",
                         role="admin", badge_number="ADM-001")
            admin.set_password("admin123")
            db.session.add(admin)
        if not User.query.filter_by(username="officer1").first():
            officer = User(name="Officer Ravi Kumar", username="officer1", email="ravi@cms.gov.in",
                            role="officer", badge_number="PO-1042", phone="9876543210")
            officer.set_password("officer123")
            db.session.add(officer)
        db.session.commit()

    app.run(debug=True, host="0.0.0.0", port=5000)
