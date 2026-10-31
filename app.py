import os
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, func


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
db = SQLAlchemy()


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.String(36), nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    difficulty = db.Column(db.String(10), nullable=False, default="medium")
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    tasks = db.relationship(
        "StudyTask", backref="subject", cascade="all, delete-orphan", lazy=True
    )
    __table_args__ = (UniqueConstraint("owner_id", "name", name="uq_subject_owner_name"),)


class StudyTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.String(36), nullable=False, index=True)
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subject.id", ondelete="CASCADE"), nullable=False
    )
    title = db.Column(db.String(120), nullable=False)
    study_date = db.Column(db.Date, nullable=False)
    minutes = db.Column(db.Integer, nullable=False, default=30)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


def create_app(test_config=None):
    app = Flask(__name__)
    default_db = f"sqlite:///{BASE_DIR / 'instance' / 'exam_planner.db'}"
    database_url = os.getenv("DATABASE_URL", default_db)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY") or os.getenv("SESSION_SECRET", "dev-only-change-this-secret"),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
        (BASE_DIR / "instance").mkdir(exist_ok=True)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    def current_owner_id():
        if "owner_id" not in session:
            session["owner_id"] = str(uuid.uuid4())
        return session["owner_id"]

    @app.get("/")
    def index():
        owner_id = current_owner_id()
        today = date.today()
        subjects = (
            Subject.query.filter_by(owner_id=owner_id)
            .order_by(Subject.exam_date.asc(), Subject.name.asc())
            .all()
        )
        tasks = (
            StudyTask.query.filter_by(owner_id=owner_id)
            .order_by(StudyTask.completed.asc(), StudyTask.study_date.asc(), StudyTask.id.asc())
            .all()
        )
        upcoming_subjects = [subject for subject in subjects if subject.exam_date >= today]
        pending_tasks = [task for task in tasks if not task.completed]
        return render_template(
            "index.html",
            subjects=subjects,
            tasks=tasks,
            today=today,
            next_exam=upcoming_subjects[0] if upcoming_subjects else None,
            pending_count=len(pending_tasks),
            completed_count=len(tasks) - len(pending_tasks),
        )

    @app.post("/subjects")
    def add_subject():
        owner_id = current_owner_id()
        name = request.form.get("name", "").strip()
        exam_date_value = request.form.get("exam_date", "")
        difficulty = request.form.get("difficulty", "medium")
        if not name or len(name) > 80:
            flash("Enter a subject name (up to 80 characters).", "error")
            return redirect(url_for("index"))
        if difficulty not in {"easy", "medium", "hard"}:
            flash("Choose a valid difficulty level.", "error")
            return redirect(url_for("index"))
        try:
            exam_date = date.fromisoformat(exam_date_value)
        except ValueError:
            flash("Choose a valid exam date.", "error")
            return redirect(url_for("index"))
        duplicate = Subject.query.filter(
            Subject.owner_id == owner_id, func.lower(Subject.name) == name.lower()
        ).first()
        if duplicate:
            flash("That subject is already on your list.", "error")
            return redirect(url_for("index"))

        db.session.add(
            Subject(owner_id=owner_id, name=name, exam_date=exam_date, difficulty=difficulty)
        )
        db.session.commit()
        flash(f"{name} added to your exam list.", "success")
        return redirect(url_for("index"))

    @app.post("/subjects/<int:subject_id>/delete")
    def delete_subject(subject_id):
        subject = Subject.query.filter_by(
            id=subject_id, owner_id=current_owner_id()
        ).first_or_404()
        db.session.delete(subject)
        db.session.commit()
        flash(f"{subject.name} and its revision tasks were removed.", "success")
        return redirect(url_for("index"))

    @app.post("/tasks")
    def add_task():
        owner_id = current_owner_id()
        title = request.form.get("title", "").strip()
        study_date_value = request.form.get("study_date", "")
        try:
            subject_id = int(request.form.get("subject_id", ""))
            minutes = int(request.form.get("minutes", "30"))
            study_date = date.fromisoformat(study_date_value)
        except (TypeError, ValueError):
            flash("Choose a subject, study date, and valid duration.", "error")
            return redirect(url_for("index"))
        subject = Subject.query.filter_by(id=subject_id, owner_id=owner_id).first()
        if not subject:
            flash("Choose one of your subjects for this task.", "error")
            return redirect(url_for("index"))
        if not title or len(title) > 120:
            flash("Enter a revision topic (up to 120 characters).", "error")
        elif not 10 <= minutes <= 300:
            flash("Study time must be between 10 and 300 minutes.", "error")
        else:
            db.session.add(
                StudyTask(
                    owner_id=owner_id,
                    subject_id=subject.id,
                    title=title,
                    study_date=study_date,
                    minutes=minutes,
                )
            )
            db.session.commit()
            flash("Revision task added.", "success")
        return redirect(url_for("index"))

    @app.post("/tasks/<int:task_id>/toggle")
    def toggle_task(task_id):
        task = StudyTask.query.filter_by(
            id=task_id, owner_id=current_owner_id()
        ).first_or_404()
        task.completed = not task.completed
        db.session.commit()
        return redirect(url_for("index"))

    @app.post("/tasks/<int:task_id>/delete")
    def delete_task(task_id):
        task = StudyTask.query.filter_by(
            id=task_id, owner_id=current_owner_id()
        ).first_or_404()
        db.session.delete(task)
        db.session.commit()
        flash("Revision task removed.", "success")
        return redirect(url_for("index"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
