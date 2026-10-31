# Studywell Exam Planner

## Run on Replit

- Existing Python 3.12 / Flask application; keep its current structure.
- Click Run to start the `Start application` workflow (`python app.py`).
- The server listens on `0.0.0.0:5000` and appears in Preview.
- Dependencies are declared in `requirements.txt`.
- Debug mode is disabled by default. Set `FLASK_DEBUG=true` only for local development if needed.

## Configuration and data

- Flask uses `SECRET_KEY` when supplied, otherwise the existing Replit `SESSION_SECRET`. Never commit secret values.
- With no `DATABASE_URL`, data is stored in `instance/exam_planner.db` (SQLite). This directory is excluded from Git.
- Keep SQLite for this development setup. The original app also supports an explicitly configured PostgreSQL database; do not replace its database without approval.
- Plans belong to a browser session, not a student account. Clearing cookies loses access to that browser's plans; plans do not sync across devices.
- This is a development setup, not a production deployment. Review persistent database storage and production serving before publishing for real users.

## Verification

Run `python -m unittest discover -s tests -v` for the existing planner tests.
