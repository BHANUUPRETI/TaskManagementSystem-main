# seed.py
"""
Database seed script for TMS API.
Run this after initializing the database (after `python run.py`).
"""
from app import models
from app import db
from app import auth

# Create users
user1 = models.User(username="user1")
user1.set_password("pass123")
user2 = models.User(username="user2")
user2.set_password("pass456")

# Add users to session
with db.app.app_context():
    db.db.session.add_all([user1, user2])
    db.db.session.commit()

    # Create projects
    project1 = models.Project(name="Project Alpha", owner_id=user1.id)
    project2 = models.Project(name="Project Beta", owner_id=user2.id)
    db.db.session.add_all([project1, project2])
    db.db.session.commit()

    # Create tasks
    task1 = models.Task(title="Setup repo", description="Initialize git repository", project_id=project1.id, assigned_to=user1.id, status="Pending")
    task2 = models.Task(title="Design DB", description="Design the database schema", project_id=project1.id, assigned_to=user2.id, status="Pending")
    task3 = models.Task(title="Implement API", description="Develop REST endpoints", project_id=project1.id, assigned_to=user1.id, status="Pending")
    db.db.session.add_all([task1, task2, task3])
    db.db.session.commit()

    # Add dependencies (task3 depends on task2)
    task3.dependencies.append(task2)
    db.db.session.commit()

    print("Seed data inserted successfully.")
