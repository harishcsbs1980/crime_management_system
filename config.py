import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production")
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # ---------------------------------------------------------------
    # Database
    # ---------------------------------------------------------------
    # By default the app runs on SQLite so it works out of the box with
    # zero setup. To use MySQL in production, set USE_MYSQL=1 and fill
    # in the MYSQL_* environment variables (or edit the defaults below).
    USE_MYSQL = os.environ.get("USE_MYSQL", "0") == "1"

    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "password")
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")
    MYSQL_DB = os.environ.get("MYSQL_DB", "crime_management_system")

    if USE_MYSQL:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@"
            f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
        )
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'crime_management.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB max upload
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "docx", "mp4", "txt"}
