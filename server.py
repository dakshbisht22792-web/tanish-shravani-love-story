import json
import os
import sqlite3
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DB_PATH = os.path.join(BASE_DIR, "tasks.db")

VALID_STATUSES = {"To Do", "In Progress", "Completed"}
VALID_PRIORITIES = {"High", "Medium", "Low"}


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT NOT NULL CHECK (status IN ('To Do', 'In Progress', 'Completed')),
                priority TEXT NOT NULL CHECK (priority IN ('High', 'Medium', 'Low')),
                category TEXT DEFAULT '',
                due_date TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class TaskHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict | list, status: int = HTTPStatus.OK) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, text: str, status: int = HTTPStatus.OK, content_type: str = "text/plain; charset=utf-8") -> None:
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None

        if length <= 0:
            return None

        body = self.rfile.read(length)
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return None

    def _validate_task_payload(self, payload: dict, partial: bool = False) -> tuple[bool, str]:
        required = ["title", "status", "priority"]
        if not partial:
            missing = [key for key in required if key not in payload]
            if missing:
                return False, f"Missing fields: {', '.join(missing)}"

        if "title" in payload and not str(payload["title"]).strip():
            return False, "Title cannot be empty"

        if "status" in payload and payload["status"] not in VALID_STATUSES:
            return False, "Invalid status"

        if "priority" in payload and payload["priority"] not in VALID_PRIORITIES:
            return False, "Invalid priority"

        if "due_date" in payload and payload["due_date"]:
            try:
                datetime.strptime(payload["due_date"], "%Y-%m-%d")
            except ValueError:
                return False, "due_date must be YYYY-MM-DD"

        return True, ""

    def _serialize_task(self, row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "status": row["status"],
            "priority": row["priority"],
            "category": row["category"],
            "due_date": row["due_date"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/tasks":
            params = parse_qs(parsed.query)
            status = params.get("status", [""])[0]
            priority = params.get("priority", [""])[0]
            category = params.get("category", [""])[0]

            query = "SELECT * FROM tasks WHERE 1=1"
            values: list[str] = []

            if status:
                query += " AND status = ?"
                values.append(status)
            if priority:
                query += " AND priority = ?"
                values.append(priority)
            if category:
                query += " AND category = ?"
                values.append(category)

            query += " ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, due_date ASC, id DESC"

            with get_connection() as conn:
                rows = conn.execute(query, values).fetchall()

            self._send_json([self._serialize_task(row) for row in rows])
            return

        if path == "/api/categories":
            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT DISTINCT category FROM tasks WHERE category != '' ORDER BY category COLLATE NOCASE"
                ).fetchall()
            self._send_json([row["category"] for row in rows])
            return

        # Static files
        if path == "/":
            path = "/index.html"

        full_path = os.path.normpath(os.path.join(STATIC_DIR, path.lstrip("/")))
        if not full_path.startswith(STATIC_DIR):
            self._send_text("Forbidden", status=HTTPStatus.FORBIDDEN)
            return

        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            self._send_text("Not Found", status=HTTPStatus.NOT_FOUND)
            return

        content_type = "text/plain; charset=utf-8"
        if full_path.endswith(".html"):
            content_type = "text/html; charset=utf-8"
        elif full_path.endswith(".css"):
            content_type = "text/css; charset=utf-8"
        elif full_path.endswith(".js"):
            content_type = "application/javascript; charset=utf-8"

        with open(full_path, "rb") as f:
            data = f.read()

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        if self.path != "/api/tasks":
            self._send_json({"error": "Not Found"}, HTTPStatus.NOT_FOUND)
            return

        payload = self._read_json()
        if payload is None:
            self._send_json({"error": "Invalid JSON body"}, HTTPStatus.BAD_REQUEST)
            return

        valid, message = self._validate_task_payload(payload)
        if not valid:
            self._send_json({"error": message}, HTTPStatus.BAD_REQUEST)
            return

        now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        task_values = (
            payload["title"].strip(),
            str(payload.get("description", "")).strip(),
            payload["status"],
            payload["priority"],
            str(payload.get("category", "")).strip(),
            str(payload.get("due_date", "")).strip(),
            now,
            now,
        )

        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO tasks (title, description, status, priority, category, due_date, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                task_values,
            )
            task_id = cur.lastrowid
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

        self._send_json(self._serialize_task(row), HTTPStatus.CREATED)

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) != 3 or path_parts[0] != "api" or path_parts[1] != "tasks":
            self._send_json({"error": "Not Found"}, HTTPStatus.NOT_FOUND)
            return

        try:
            task_id = int(path_parts[2])
        except ValueError:
            self._send_json({"error": "Invalid task ID"}, HTTPStatus.BAD_REQUEST)
            return

        payload = self._read_json()
        if payload is None:
            self._send_json({"error": "Invalid JSON body"}, HTTPStatus.BAD_REQUEST)
            return

        valid, message = self._validate_task_payload(payload, partial=True)
        if not valid:
            self._send_json({"error": message}, HTTPStatus.BAD_REQUEST)
            return

        fields = []
        values = []
        allowed_fields = ["title", "description", "status", "priority", "category", "due_date"]

        for field in allowed_fields:
            if field in payload:
                fields.append(f"{field} = ?")
                if field in {"title", "description", "category", "due_date"}:
                    values.append(str(payload[field]).strip())
                else:
                    values.append(payload[field])

        if not fields:
            self._send_json({"error": "No fields to update"}, HTTPStatus.BAD_REQUEST)
            return

        values.append(datetime.utcnow().isoformat(timespec="seconds") + "Z")
        values.append(task_id)

        with get_connection() as conn:
            existing = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not existing:
                self._send_json({"error": "Task not found"}, HTTPStatus.NOT_FOUND)
                return

            conn.execute(
                f"UPDATE tasks SET {', '.join(fields)}, updated_at = ? WHERE id = ?",
                values,
            )
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

        self._send_json(self._serialize_task(row), HTTPStatus.OK)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) != 3 or path_parts[0] != "api" or path_parts[1] != "tasks":
            self._send_json({"error": "Not Found"}, HTTPStatus.NOT_FOUND)
            return

        try:
            task_id = int(path_parts[2])
        except ValueError:
            self._send_json({"error": "Invalid task ID"}, HTTPStatus.BAD_REQUEST)
            return

        with get_connection() as conn:
            existing = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not existing:
                self._send_json({"error": "Task not found"}, HTTPStatus.NOT_FOUND)
                return

            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

        self._send_json({"success": True}, HTTPStatus.OK)

    def log_message(self, format: str, *args) -> None:
        return


def run(host: str = "127.0.0.1", port: int = 8080) -> None:
    init_db()
    server = ThreadingHTTPServer((host, port), TaskHandler)
    print(f"Task Manager running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
