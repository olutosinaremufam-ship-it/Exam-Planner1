import unittest
from datetime import date

from app import create_app, db


class ExamPlannerTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_dashboard_loads_for_new_student(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Your subjects", response.data)
        self.assertIn(b"Revision plan", response.data)

    def test_student_can_add_subject_and_revision_task(self):
        response = self.client.post(
            "/subjects",
            data={"name": "Biology", "exam_date": date.today().isoformat(), "difficulty": "hard"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Biology", response.data)

        with self.app.app_context():
            from app import Subject

            subject = Subject.query.one()
            subject_id = subject.id

        response = self.client.post(
            "/tasks",
            data={
                "subject_id": str(subject_id),
                "title": "Cell structure",
                "study_date": date.today().isoformat(),
                "minutes": "45",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Cell structure", response.data)
        self.assertIn(b"45 min", response.data)

    def test_student_can_complete_and_remove_revision_task(self):
        self.client.post(
            "/subjects",
            data={"name": "Chemistry", "exam_date": date.today().isoformat(), "difficulty": "medium"},
        )
        with self.app.app_context():
            from app import Subject

            subject_id = Subject.query.one().id
        self.client.post(
            "/tasks",
            data={
                "subject_id": str(subject_id),
                "title": "Atomic structure",
                "study_date": date.today().isoformat(),
                "minutes": "30",
            },
        )
        with self.app.app_context():
            from app import StudyTask

            task_id = StudyTask.query.one().id
        self.client.post(f"/tasks/{task_id}/toggle")
        response = self.client.get("/")
        self.assertIn(b'class="stat-label">COMPLETED</span><strong>1', response.data)
        self.client.post(f"/tasks/{task_id}/delete")
        self.assertEqual(self.client.get("/").status_code, 200)
        with self.app.app_context():
            from app import StudyTask

            self.assertEqual(StudyTask.query.count(), 0)

    def test_subjects_are_isolated_between_browser_sessions(self):
        self.client.post(
            "/subjects",
            data={"name": "Physics", "exam_date": date.today().isoformat(), "difficulty": "easy"},
        )
        other_browser = self.app.test_client()
        response = other_browser.get("/")
        self.assertNotIn(b"Physics", response.data)

    def test_invalid_task_duration_is_rejected(self):
        self.client.post(
            "/subjects",
            data={"name": "History", "exam_date": date.today().isoformat(), "difficulty": "medium"},
        )
        with self.app.app_context():
            from app import Subject

            subject_id = Subject.query.one().id
        response = self.client.post(
            "/tasks",
            data={
                "subject_id": str(subject_id),
                "title": "Read chapter",
                "study_date": date.today().isoformat(),
                "minutes": "500",
            },
            follow_redirects=True,
        )
        self.assertIn(b"between 10 and 300 minutes", response.data)


if __name__ == "__main__":
    unittest.main()
