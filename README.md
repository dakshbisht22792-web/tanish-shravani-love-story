# Task Manager App

A local web app with full CRUD task management using SQLite for persistent storage.

## Features

- Full CRUD operations: create, read, update, delete tasks
- Priority levels: High, Medium, Low with color coding
- Status tracking: To Do, In Progress, Completed
- Custom categories per task
- Filtering by status, priority, and category
- Due dates with clear display on each task
- SQLite database (`tasks.db`) for persistent local storage
- Clean, responsive UI

## Run

1. Open a terminal in `task-manager-app`
2. Run:

```powershell
python server.py
```

3. Open:

```text
http://127.0.0.1:8080
```

## Project Structure

- `server.py`: API + static file server + SQLite setup
- `static/index.html`: app UI
- `static/styles.css`: responsive styling
- `static/app.js`: frontend logic and API integration
- `tasks.db`: created automatically on first run
