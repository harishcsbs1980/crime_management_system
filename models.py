from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="officer")  # admin | officer
    badge_number = db.Column(db.String(40), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cases_assigned = db.relationship("Case", backref="officer", lazy=True,
                                      foreign_keys="Case.officer_id")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"


class Complainant(db.Model):
    __tablename__ = "complainants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    firs = db.relationship("FIR", backref="complainant", lazy=True)


class FIR(db.Model):
    __tablename__ = "firs"

    id = db.Column(db.Integer, primary_key=True)
    fir_number = db.Column(db.String(40), unique=True, nullable=False)
    crime_type = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    date_of_incident = db.Column(db.Date, nullable=False, default=date.today)
    date_filed = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="Registered")
    # Registered -> Under Investigation -> Charge Sheet Filed -> In Court -> Closed
    complainant_id = db.Column(db.Integer, db.ForeignKey("complainants.id"), nullable=False)
    filed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    case = db.relationship("Case", backref="fir", uselist=False, lazy=True)
    filed_by = db.relationship("User", foreign_keys=[filed_by_id])


class Case(db.Model):
    __tablename__ = "cases"

    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(40), unique=True, nullable=False)
    fir_id = db.Column(db.Integer, db.ForeignKey("firs.id"), nullable=False)
    officer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    status = db.Column(db.String(30), default="Open")  # Open | Investigating | Closed
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(20), default="Medium")  # Low | Medium | High
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)

    evidences = db.relationship("Evidence", backref="case", lazy=True, cascade="all, delete-orphan")
    witnesses = db.relationship("Witness", backref="case", lazy=True, cascade="all, delete-orphan")
    notes = db.relationship("InvestigationNote", backref="case", lazy=True, cascade="all, delete-orphan")
    court_records = db.relationship("CourtRecord", backref="case", lazy=True, cascade="all, delete-orphan")
    charge_sheet = db.relationship("ChargeSheet", backref="case", uselist=False, lazy=True,
                                    cascade="all, delete-orphan")


class Evidence(db.Model):
    __tablename__ = "evidence"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("cases.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(255), nullable=True)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    uploaded_by = db.relationship("User", foreign_keys=[uploaded_by_id])


class Witness(db.Model):
    __tablename__ = "witnesses"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("cases.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    statement = db.Column(db.Text, nullable=False)
    recorded_on = db.Column(db.DateTime, default=datetime.utcnow)


class InvestigationNote(db.Model):
    __tablename__ = "investigation_notes"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("cases.id"), nullable=False)
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    created_by = db.relationship("User", foreign_keys=[created_by_id])


class ChargeSheet(db.Model):
    __tablename__ = "charge_sheets"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("cases.id"), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    filed_on = db.Column(db.DateTime, default=datetime.utcnow)


class CourtRecord(db.Model):
    __tablename__ = "court_records"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("cases.id"), nullable=False)
    hearing_date = db.Column(db.Date, nullable=False)
    court_status = db.Column(db.String(40), default="Scheduled")  # Scheduled|Adjourned|Judgment
    judge_name = db.Column(db.String(120), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    judgment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id])
