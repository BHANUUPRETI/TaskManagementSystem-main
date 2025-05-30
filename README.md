# Task Management System (TMS) API

This is a Flask-based RESTful API for managing users, projects, and tasks with support for authentication, task dependencies, and pagination.

## Features
- User registration and login (JWT authentication)
- CRUD operations for users, projects, and tasks
- Task dependencies with cycle detection
- Pagination for list endpoints

## Requirements
- Python 3.10+
- pip

## Setup Instructions

1. **Open zip file**

     ```
     extract zip file
     cd TMS
     ```

2. **Create a virtual environment (optional but recommended)**

     ```
     python -m venv venv
     .\venv\Scripts\activate  # On Windows
     # Or
     source venv/bin/activate  # On Linux/Mac
     ```

3. **Install dependencies**

     ```
     pip install -r requirements.txt
     ```

4. **Set up the database**

     - The app uses SQLAlchemy. By default, it uses SQLite. You can configure the database URI in `app/config.py`.

     ### Option 1: Use SQLite (default)

     To initialize the database, run:

     ```
     python run.py
     ```

     This will create the necessary tables if they do not exist.

     ### Option 2: Use PostgreSQL with Docker (recommended for development)

     You can run a PostgreSQL database using Docker:

     ```
     docker run --name taskdb -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -p 5432:5432 -d postgres
     ```

     Or use Docker Compose (recommended):

     1. Make sure you have Docker and Docker Compose installed.
     2. In the project root, run:

          ```
          docker-compose up -d
          ```

     This will start a PostgreSQL container named `taskdb` with the correct credentials and port mapping.

     - The database will be accessible at `localhost:5432` with user `postgres` and password `postgres`.
     - Set the database name to `taskdb` in your `.env` file and update `SQLALCHEMY_DATABASE_URI` in `app/config.py` accordingly.

     Migration Commands
     Run the following to set up your database:

     ```
     flask db init
     flask db migrate -m "Initial migration"
     flask db upgrade
     ```

     After setting up the database, run:

     ```
     python run.py
     ```

     This will create the necessary tables if they do not exist.

5. **Run the application**

     ```
     python run.py
     ```

     The API will be available at `http://127.0.0.1:5000/`.
     

## API Usage

### Authentication

- **Register:**

  ```
  curl -X POST http://127.0.0.1:5000/auth/register \
           -H "Content-Type: application/json" \
           -d '{"username": "user1", "password": "pass123"}'
  ```

- **Login:**

  ```
  curl -X POST http://127.0.0.1:5000/auth/login \
           -H "Content-Type: application/json" \
           -d '{"username": "user1", "password": "pass123"}'
  ```

Response will include a JWT token. Use this token for all protected endpoints:

```
-H "Authorization: Bearer <token>"
```

### Example: Create a Project

```
curl -X POST http://127.0.0.1:5000/projects \
       -H "Content-Type: application/json" \
       -H "Authorization: Bearer <token>" \
       -d '{"name": "Project Alpha"}'
```

### Example: Create a Task

```
curl -X POST http://127.0.0.1:5000/tasks \
       -H "Content-Type: application/json" \
       -H "Authorization: Bearer <token>" \
       -d '{
                 "title": "Task 1",
                 "description": "Description here",
                 "project_id": 1,
                 "assigned_to": 1,
                 "status": "Pending",
                 "dependencies": []
               }'
```

### Example: Get All Users (paginated)

```
curl -X GET "http://127.0.0.1:5000/users?page=1&per_page=10" \
       -H "Authorization: Bearer <token>"
```

### Using Postman

1. Import the API endpoints manually or use the above curl commands in the Postman interface.
2. For protected endpoints, add an `Authorization` header:
     - Key: `Authorization`
     - Value: `Bearer <token>`

## Running Tests

If you have test files (e.g., `test_task_dependency.py`), run:

```
python test_task_dependency.py
```

## Notes

- Update `app/config.py` for custom database settings.
- For more endpoints and details, see the code in `app/routes.py`.

---

Feel free to extend the API or add a frontend as needed.
