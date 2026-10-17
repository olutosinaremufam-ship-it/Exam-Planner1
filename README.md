# Studywell Exam Planner

A small Flask app for keeping exam subjects, exam dates, and revision sessions together. It uses Bootstrap 5 for responsive layout, SQLAlchemy for persistence, SQLite by default, and Supabase PostgreSQL when `DATABASE_URL` is configured.

## MVP Phases

1. **Phase 1: Exam planner MVP (this build)** — add subjects, exam dates, and difficulty; create dated revision tasks with a duration; mark tasks complete; see the next exam and progress counts. Data is separated by browser session. There is no account system yet.
2. **Phase 2: Student accounts** — add sign-up, login, password reset, and permanent student-owned data so plans work across devices.
3. **Phase 3: Better study planning** — weekly availability, automatically suggested revision blocks, recurring sessions, filters, and calendar view.
4. **Phase 4: Learning tools** — topic notes, flashcards, quizzes, and progress summaries for each subject.
5. **Phase 5: Launch readiness** — database migrations, security review, backups, accessibility checks, automated deployment, and monitoring.

## Run in VS Code

1. Install Python 3.10 or newer.
2. Open this folder in VS Code and create a virtual environment in the integrated terminal:

   ```bash
   python -m venv .venv
   ```

3. Activate it:

   - Windows PowerShell: `.venv\\Scripts\\Activate.ps1`
   - macOS/Linux: `source .venv/bin/activate`

4. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Optional: copy `.env.example` to `.env`. Without a `DATABASE_URL`, the app creates a local SQLite database in `instance/exam_planner.db`.
6. Start the server:

   ```bash
   python app.py
   ```

7. Open <http://127.0.0.1:5000> in your browser. Stop the server with `Ctrl+C`.

## Connect Supabase PostgreSQL

1. Create a Supabase project.
2. In the Supabase dashboard open **Project Settings → Database** and copy a PostgreSQL connection string. Use the direct or session-pooler connection, not a transaction-pooler URL for this simple SQLAlchemy setup.
3. Copy `.env.example` to `.env` and set `DATABASE_URL` to that connection string. If the password contains reserved URL characters, URL-encode them first.
4. Set `SECRET_KEY` to a long, random value. Keep `.env` private; it is excluded from Git.
5. Run `python app.py`. The MVP creates its tables at startup. Use the Supabase connection string recommended for your network/IPv4 environment.

The application accepts `postgresql://` or `postgres://` URLs and uses the Psycopg 3 driver. Keep the database password out of source code and never commit `.env`.

## MVP Scope and limitations

This first version intentionally has no sign-in, automated timetable, email reminders, or file uploads. A signed browser session keeps one visitor's records separate from another visitor, but clearing that browser's session cookie means those records are no longer associated with that browser. Add Phase 2 authentication before treating this as a multi-device or public student service. Bootstrap and Google Fonts are loaded from CDNs, so those assets require an internet connection.

## Tests

```bash
python -m unittest discover -s tests -v
```
