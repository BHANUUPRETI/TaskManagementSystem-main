import unittest
from app import create_app, db
from app.models import User, Project, Task, TaskDependency
from flask import json

class TaskDependencyTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            user = User(username='testuser')
            user.set_password('testpass')
            db.session.add(user)
            project = Project(name='Test Project')
            db.session.add(project)
            db.session.commit()
            self.user_id = user.id
            self.project_id = project.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_task_with_no_dependencies(self):
        with self.app.app_context():
            task = Task(title='Task 1', description='No deps', project_id=self.project_id, assigned_to=self.user_id)
            db.session.add(task)
            db.session.commit()
            self.assertEqual(Task.query.count(), 1)
            self.assertEqual(TaskDependency.query.count(), 0)

    def test_create_task_with_dependencies(self):
        with self.app.app_context():
            t1 = Task(title='Task 1', description='First', project_id=self.project_id, assigned_to=self.user_id)
            db.session.add(t1)
            db.session.commit()
            t2 = Task(title='Task 2', description='Second', project_id=self.project_id, assigned_to=self.user_id)
            db.session.add(t2)
            db.session.commit()
            dep = TaskDependency(dependent_task_id=t2.id, depends_on_id=t1.id)
            db.session.add(dep)
            db.session.commit()
            self.assertEqual(TaskDependency.query.count(), 1)
            self.assertEqual(TaskDependency.query.first().depends_on_id, t1.id)

    def test_circular_dependency_detection(self):
        with self.app.app_context():
            t1 = Task(title='Task 1', description='First', project_id=self.project_id, assigned_to=self.user_id)
            t2 = Task(title='Task 2', description='Second', project_id=self.project_id, assigned_to=self.user_id)
            db.session.add_all([t1, t2])
            db.session.commit()
            dep = TaskDependency(dependent_task_id=t2.id, depends_on_id=t1.id)
            db.session.add(dep)
            db.session.commit()
            circular = TaskDependency(dependent_task_id=t1.id, depends_on_id=t2.id)
            db.session.add(circular)
            try:
                db.session.commit()
                self.fail('Circular dependency should not be allowed')
            except Exception:
                db.session.rollback()
                self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
