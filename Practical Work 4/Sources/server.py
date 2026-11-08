import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

DATABASE = os.environ.get("COURSEHUB_DB", "/data/coursehub.sqlite")
HOST = os.environ.get("COURSEHUB_HOST", "0.0.0.0")
PORT = int(os.environ.get("COURSEHUB_PORT", "8080"))


class CourseHubHandler(BaseHTTPRequestHandler):
    def respond(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != "/registrations":
            self.respond(404, {"error": "Unknown endpoint"})
            return

        with closing(sqlite3.connect(DATABASE)) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                "SELECT student_id, course_id, created_at FROM registrations "
                "ORDER BY student_id, course_id"
            ).fetchall()
        self.respond(200, [dict(row) for row in rows])

    def do_POST(self):
        if self.path != "/registrations":
            self.respond(404, {"error": "Unknown endpoint"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError
            payload = json.loads(self.rfile.read(length))
            student = payload["student_id"]
            course = payload["course_id"]
            if not all(isinstance(value, str) and value.strip() and len(value) <= 64
                       for value in (student, course)):
                raise ValueError
        except (ValueError, TypeError, KeyError):
            self.respond(400, {"error": "Expected student_id and course_id strings"})
            return

        created_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        with closing(sqlite3.connect(DATABASE)) as db, db:
            try:
                db.execute("INSERT INTO registrations VALUES (?, ?, ?)",
                           (student, course, created_at))
            except sqlite3.IntegrityError:
                self.respond(409, {"error": "Registration already exists"})
                return

        self.respond(201, {"student_id": student, "course_id": course,
                           "created_at": created_at})


if __name__ == "__main__":
    with closing(sqlite3.connect(DATABASE)) as db, db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS registrations ("
            "student_id TEXT NOT NULL, course_id TEXT NOT NULL, "
            "created_at TEXT NOT NULL, PRIMARY KEY (student_id, course_id))"
        )
    with HTTPServer((HOST, PORT), CourseHubHandler) as server:
        server.serve_forever()
