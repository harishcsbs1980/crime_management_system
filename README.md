# Crime Management System

A full-stack web application for police departments to digitize FIR
registration, case assignment, investigation, evidence management, court
proceedings, case closure, and crime analytics — built with **Flask**,
**SQLAlchemy**, and **MySQL** (SQLite by default for zero-setup local runs).

## Features

- Secure login with hashed passwords (Flask-Login + Werkzeug)
- Role-based access: **Admin** (full control) and **Police Officer** (assigned cases)
- FIR registration, search, filter, edit
- Case creation & officer assignment from an FIR
- Investigation workspace per case: evidence upload, witness statements,
  investigation notes, charge sheet filing, court hearing tracking
- Case status lifecycle: Open → Investigating → Closed
- Dashboard with live stats and Chart.js analytics (FIR trend, case status split)
- Reports page: crime-type distribution, case priority split, officer caseload, clearance rate
- Admin-only user management (create/edit/disable officers & admins)
- Responsive UI, works down to mobile widths
- Activity log of key actions (logins, FIR filings, case creation)

## Tech Stack

| Layer     | Technology                                  |
|-----------|----------------------------------------------|
| Frontend  | HTML, CSS (custom design system), vanilla JS, Chart.js |
| Backend   | Python, Flask, Flask-Login, Flask-SQLAlchemy |
| Database  | MySQL (production) / SQLite (default, zero-setup) |

## Getting Started (Quick / SQLite)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

flask --app app init-db         # creates tables + seed admin/officer accounts
python app.py                   # or: flask --app app run
```

Visit **http://localhost:5000** and sign in with:

| Role    | Username  | Password  |
|---------|-----------|-----------|
| Admin   | admin     | admin123  |
| Officer | officer1  | officer123 |

> Change these passwords immediately in a real deployment (Settings page,
> or the User Management screen for other accounts).

## Switching to MySQL

1. Create the database — either let SQLAlchemy do it, or run the provided schema:
   ```bash
   mysql -u root -p < schema_mysql.sql
   ```
2. Set environment variables (e.g. in a `.env` file — see `.env.example`):
   ```
   USE_MYSQL=1
   MYSQL_USER=root
   MYSQL_PASSWORD=yourpassword
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_DB=crime_management_system
   SECRET_KEY=some-long-random-string
   ```
3. Install `PyMySQL` (already in `requirements.txt`), then run:
   ```bash
   flask --app app init-db
   python app.py
   ```

## Project Structure

```
crime_management_system/
├── app.py                 # Routes, auth, business logic
├── models.py               # SQLAlchemy models (Users, FIR, Case, Evidence, ...)
├── config.py                # SQLite/MySQL config switch
├── utils.py                  # Decorators & helpers (admin_required, reference numbers)
├── requirements.txt
├── schema_mysql.sql         # Hand-written MySQL DDL, mirrors models.py
├── static/
│   ├── css/style.css        # Design system ("case file" visual identity)
│   ├── js/main.js           # Sidebar toggle, flash auto-dismiss, tabs
│   └── uploads/             # Evidence / charge-sheet file uploads (created at runtime)
└── templates/
    ├── base.html             # Sidebar shell layout
    ├── login.html
    ├── dashboard.html
    ├── fir_list.html / fir_form.html / fir_detail.html
    ├── case_list.html / case_detail.html
    ├── reports.html
    ├── user_list.html / user_form.html
    ├── settings.html
    └── 404.html / 403.html
```

## Roles & Permissions

- **Admin**: manage users, assign officers to cases, view/delete all FIRs, full reports access.
- **Police Officer**: view/investigate only the cases assigned to them, add evidence/witnesses/notes,
  file charge sheets, log court hearings, update case status.

## Notes for Production

- Set a strong, random `SECRET_KEY` via environment variable.
- Put the app behind a WSGI server (gunicorn/uWSGI) + reverse proxy (nginx), not `app.run()`.
- Serve uploaded evidence files from protected storage / signed URLs in a real deployment,
  rather than the public `static/uploads` folder used here for simplicity.
- Add HTTPS, rate limiting on `/login`, and audit logging retention policy as needed.
