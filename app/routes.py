from flask import *
from .models import *
from .auth import *
from functools import *
import re
import re
from werkzeug.exceptions import BadRequestKeyError
from sqlalchemy.exc import SQLAlchemyError
import logging

api = Blueprint('api', __name__)

# LOGIN
@api.route('/auth/login', methods=['POST'])
def login():
    logging.info("login endpoint called")
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        logging.warning("login: missing fields")
        return jsonify({"error": "Username and password required"}), 400
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        token = generate_token(user.id)
        logging.info("login: successful for user %s", data['username'])
        return jsonify({"token": token}), 200
    logging.warning("login: invalid credentials for user %s", data.get('username'))
    return jsonify({"error": "Invalid credentials"}), 401


# USERS
@api.route('/create_users', methods=['POST'])
def create_users():
    logging.info("create_users endpoint called")
    try:
        data = request.json
        if not data or not all(k in data for k in ('username', 'email', 'password')):
            logging.warning("create_users: missing required fields")
            return jsonify({'error': 'Missing required fields'}), 400
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            logging.warning("create_users: invalid email format: %s", data['email'])
            return jsonify({'error': 'Invalid email format'}), 400
    except BadRequestKeyError:
        logging.warning("create_users: missing JSON payload")
        return jsonify({'error': 'Missing JSON payload'}), 400

    if User.query.filter_by(username=data['username']).first():
        logging.warning("create_users: user already exists: %s", data['username'])
        return jsonify({"error": "User already exists"}), 409
    try:
        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        logging.info("User created: %s", data['username'])
        return jsonify({"message": "User created successfully", "user_id": user.id}), 201
    except SQLAlchemyError:
        db.session.rollback()
        logging.error("Database error occurred in create_users", exc_info=True)
        return jsonify({"error": "Database error"}), 500


@api.route('/list_users', methods=['GET'])
@token_required
def list_users(user_id):
    logging.info("list_users endpoint called by user_id %s", user_id)
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        pagination = User.query.paginate(page=page, per_page=per_page, error_out=False)
        users = [{'id': user.id, 'username': user.username} for user in pagination.items]
        logging.info("list_users: returned %d users", len(users))
        return jsonify({
            'users': users,
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages
        }), 200
    except SQLAlchemyError:
        logging.error("Database error occurred in list_users", exc_info=True)
        return jsonify({'error': 'Database error'}), 500


@api.route('/get_users/<int:target_user_id>', methods=['GET'])
@token_required
def get_users(user_id, target_user_id):
    logging.info("get_users endpoint called for user_id %s", target_user_id)
    user = User.query.get(target_user_id)
    if not user:
        logging.warning("get_users: user not found: %s", target_user_id)
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'id': user.id, 'username': user.username}), 200


@api.route('/delete_users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_users(auth_user_id, user_id):
    logging.info("delete_users endpoint called for user_id %s", user_id)
    user = User.query.get(user_id)
    if not user:
        logging.warning("delete_users: user not found: %s", user_id)
        return jsonify({'error': 'User not found'}), 404
    tasks = Task.query.filter(
        Task.assigned_to == user.id,
        Task.status.in_(['Pending', 'In Progress'])
    ).all()
    if tasks:
        logging.warning("delete_users: user %s has pending/in-progress tasks", user_id)
        return jsonify({'error': 'Cannot delete user with assigned pending or in-progress tasks'}), 409
    try:
        db.session.delete(user)
        db.session.commit()
        logging.info("User deleted: %s", user_id)
        return jsonify({'message': 'User deleted successfully'}), 200
    except SQLAlchemyError:
        db.session.rollback()
        logging.error("Database error occurred in delete_users", exc_info=True)
        return jsonify({'error': 'Database error'}), 500


# PROJECTS
@api.route('/create_projects', methods=['POST'])
@token_required
def create_projects(user_id):
    logging.info("create_projects endpoint called by user_id %s", user_id)
    data = request.json
    if not data or 'name' not in data:
        logging.warning("create_projects: project name is required")
        return jsonify({'error': 'Project name is required'}), 400
    try:
        project = Project(name=data['name'])
        db.session.add(project)
        db.session.commit()
        logging.info("Project created: %s", data['name'])
        return jsonify({'message': 'Project created successfully', 'project_id': project.id}), 201
    except SQLAlchemyError:
        db.session.rollback()
        logging.error("Database error occurred in create_projects", exc_info=True)
        return jsonify({'error': 'Database error'}), 500


@api.route('/list_projects', methods=['GET'])
@token_required
def list_projects(user_id):
    logging.info("list_projects endpoint called by user_id %s", user_id)
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        pagination = Project.query.paginate(page=page, per_page=per_page, error_out=False)
        projects = [{'id': project.id, 'name': project.name} for project in pagination.items]
        logging.info("list_projects: returned %d projects", len(projects))
        return jsonify({
            'projects': projects,
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages
        }), 200
    except SQLAlchemyError:
        logging.error("Database error occurred in list_projects", exc_info=True)
        return jsonify({'error': 'Database error'}), 500


@api.route('/get_projects/<int:project_id>', methods=['GET'])
@token_required
def get_projects(user_id, project_id):
    logging.info("get_projects endpoint called for project_id %s by user_id %s", project_id, user_id)
    project = Project.query.get(project_id)
    if not project:
        logging.warning("get_projects: project not found: %s", project_id)
        return jsonify({'error': 'Project not found'}), 404
    return jsonify({'id': project.id, 'name': project.name}), 200


@api.route('/list_projects/<int:project_id>/tasks', methods=['GET'])
@token_required
def list_project_tasks(user_id, project_id):
    logging.info("list_project_tasks endpoint called for project_id %s by user_id %s", project_id, user_id)
    project = Project.query.get(project_id)
    if not project:
        logging.warning("list_project_tasks: project not found: %s", project_id)
        return jsonify({'error': 'Project not found'}), 404
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        pagination = Task.query.filter_by(project_id=project.id).paginate(page=page, per_page=per_page, error_out=False)
        tasks = [{'id': task.id, 'title': task.title, 'description': task.description} for task in pagination.items]
        logging.info("list_project_tasks: returned %d tasks for project_id %s", len(tasks), project_id)
        return jsonify({
            'tasks': tasks,
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages
        }), 200
    except SQLAlchemyError:
        logging.error("Database error occurred in list_project_tasks", exc_info=True)
        return jsonify({'error': 'Database error'}), 500


# TASKS
@api.route('/create_tasks', methods=['POST'])
@token_required
def create_tasks(user_id):
    logging.info("create_tasks endpoint called by user_id %s", user_id)
    data = request.json
    if not data or not all(k in data for k in ('title', 'description', 'project_id', 'assigned_to')):
        logging.warning("create_tasks: missing required fields")
        return jsonify({'error': 'Missing required fields'}), 400
    allowed_statuses = ['Pending', 'In Progress', 'Completed']
    status = data.get('status', 'Pending')
    if status not in allowed_statuses:
        logging.warning("create_tasks: invalid status: %s", status)
        return jsonify({'error': f'Invalid status. Allowed values: {allowed_statuses}'}), 400
    try:
        task = Task(
            title=data['title'],
            description=data['description'],
            project_id=data['project_id'],
            assigned_to=data['assigned_to'],
            status=status
        )
        db.session.add(task)
        db.session.commit()
        logging.info("Task created: %s", data['title'])
    except SQLAlchemyError:
        db.session.rollback()
        logging.error("Database error occurred in create_tasks", exc_info=True)
        return jsonify({'error': 'Database error'}), 500

    dependencies = data.get('dependencies', [])

    def has_cycle(start_id, target_id, visited=None):
        if visited is None:
            visited = set()
        if start_id == target_id:
            return True
        visited.add(start_id)
        deps = TaskDependency.query.filter_by(dependent_task_id=start_id).all()
        for dep in deps:
            if dep.depends_on_id not in visited:
                if has_cycle(dep.depends_on_id, target_id, visited):
                    return True
        return False

    try:
        for dep in dependencies:
            if has_cycle(dep, task.id):
                db.session.delete(task)
                db.session.commit()
                logging.warning("create_task: circular dependency detected for task %s", task.id)
                return jsonify({'error': 'Circular dependency detected'}), 409
            dependency = TaskDependency(dependent_task_id=task.id, depends_on_id=dep)
            db.session.add(dependency)
        db.session.commit()
        logging.info("Task dependencies set for task %s", task.id)
        return jsonify({'message': 'Task created successfully', 'task_id': task.id}), 201
    except SQLAlchemyError:
        db.session.rollback()
        logging.error("Database error occurred in create_task (dependencies)", exc_info=True)
        return jsonify({'error': 'Database error'}), 500

@api.route('/get_tasks/<int:task_id>', methods=['GET'])
@token_required
def get_tasks(user_id, task_id):
    logging.info("get_tasks endpoint called for task_id %s by user_id %s", task_id, user_id)
    try:
        task_id = int(task_id)
    except ValueError:
        logging.warning("get_tasks: invalid task_id format: %s", task_id)
        return jsonify({'error': 'Invalid task ID format'}), 400

    task = Task.query.get(task_id)
    if not task:
        logging.warning("get_tasks: task not found: %s", task_id)
        return jsonify({'error': 'Task not found'}), 404
    return jsonify({'id': task.id, 'title': task.title, 'description': task.description, 'status': task.status}), 200

@api.route('/update_tasks/<int:task_id>', methods=['PUT'])
@token_required
def update_tasks(user_id, task_id):
    logging.info("update_tasks endpoint called for task_id %s by user_id %s", task_id, user_id)
    try:
        task_id = int(task_id)
    except ValueError:
        logging.warning("update_tasks: invalid task_id format: %s", task_id)
        return jsonify({'error': 'Invalid task ID format'}), 400

    data = request.json
    task = Task.query.get(task_id)
    if not task:
        logging.warning("update_tasks: task not found: %s", task_id)
        return jsonify({'error': 'Task not found'}), 404
    allowed_statuses = ['Pending', 'In Progress', 'Completed']

    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)

    if 'dependencies' in data:
        new_dependencies = set(data['dependencies'])
        try:
            TaskDependency.query.filter_by(dependent_task_id=task.id).delete()
            db.session.flush()

            def has_cycle(start_id, target_id, visited=None):
                if visited is None:
                    visited = set()
                if start_id == target_id:
                    return True
                visited.add(start_id)
                deps = TaskDependency.query.filter_by(dependent_task_id=start_id).all()
                for dep in deps:
                    if dep.depends_on_id not in visited:
                        if has_cycle(dep.depends_on_id, target_id, visited):
                            return True
                return False

            for dep_id in new_dependencies:
                if has_cycle(dep_id, task.id):
                    db.session.rollback()
                    logging.warning("update_tasks: circular dependency detected for task %s", task.id)
                    return jsonify({'error': 'Circular dependency detected'}), 409
                dependency = TaskDependency(dependent_task_id=task.id, depends_on_id=dep_id)
                db.session.add(dependency)
        except SQLAlchemyError:
            db.session.rollback()
            logging.error("Database error occurred in update_tasks (dependencies)", exc_info=True)
            return jsonify({'error': 'Database error'}), 500

    new_status = data.get('status')
    if new_status and new_status != task.status:
        if new_status not in allowed_statuses:
            logging.warning("update_tasks: invalid status: %s", new_status)
            return jsonify({'error': f'Invalid status. Allowed values: {allowed_statuses}'}), 400
        if new_status == 'Completed':
            dependencies = TaskDependency.query.filter_by(dependent_task_id=task.id).all()
            incomplete = [
                dep.depends_on_id
                for dep in dependencies
                if Task.query.get(dep.depends_on_id).status != 'Completed'
            ]
            if incomplete:
                logging.warning("update_tasks: cannot mark as completed, dependencies incomplete for task %s", task.id)
                return jsonify({'error': 'Cannot mark as Completed. All dependencies must be completed first.'}), 409
            task.status = 'Completed'
        else:
            task.status = new_status

    try:
        db.session.commit()
        logging.info("Task updated: %s", task.id)
        return jsonify({'message': 'Task updated successfully'}), 200
    except SQLAlchemyError:
        db.session.rollback()
        logging.error("Database error occurred in update_tasks", exc_info=True)
        return jsonify({'error': 'Database error'}), 500

@api.route('/get_user_tasks', methods=['GET'])
@token_required
def get_user_tasks(user_id):
    logging.info("get_user_tasks endpoint called for user_id %s", user_id)
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        pagination = Task.query.filter_by(assigned_to=user_id).paginate(page=page, per_page=per_page, error_out=False)
        tasks = [{'id': task.id, 'title': task.title, 'description': task.description} for task in pagination.items]
        logging.info("get_user_tasks: returned %d tasks for user_id %s", len(tasks), user_id)
        return jsonify({
            'tasks': tasks,
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages
        }), 200
    except SQLAlchemyError:
        logging.error("Database error occurred in get_user_tasks", exc_info=True)
        return jsonify({'error': 'Database error'}), 500

@api.route('/get_status_tasks/<string:status>', methods=['GET'])
@token_required
def get_tasks_by_status(user_id, status):
    logging.info("get_tasks_by_status endpoint called for status %s by user_id %s", status, user_id)
    allowed_statuses = ['Pending', 'In Progress', 'Completed']
    if status not in allowed_statuses:
        logging.warning("get_tasks_by_status: invalid status: %s", status)
        return jsonify({'error': f'Invalid status. Allowed values: {allowed_statuses}'}), 400
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        pagination = Task.query.filter_by(status=status).paginate(page=page, per_page=per_page, error_out=False)
        tasks = [{'id': task.id, 'title': task.title, 'description': task.description} for task in pagination.items]
        logging.info("get_tasks_by_status: returned %d tasks for status %s", len(tasks), status)
        return jsonify({
            'tasks': tasks,
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages
        }), 200
    except SQLAlchemyError:
        logging.error("Database error occurred in get_tasks_by_status", exc_info=True)
        return jsonify({'error': 'Database error'}), 500