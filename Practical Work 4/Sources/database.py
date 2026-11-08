import os
import shutil
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path


def check(path):
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as db:
        if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise ValueError("SQLite integrity check failed")
        db.execute("SELECT student_id, course_id, created_at FROM registrations LIMIT 1")


action, database = sys.argv[1:]
if action == "backup":
    with tempfile.TemporaryDirectory() as directory:
        snapshot = Path(directory) / "backup.sqlite"
        source_uri = Path(database).resolve().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(source_uri, uri=True)) as source:
            with closing(sqlite3.connect(snapshot)) as target:
                source.backup(target)
        check(snapshot)
        with snapshot.open("rb") as stream:
            shutil.copyfileobj(stream, sys.stdout.buffer)
elif action == "restore":
    destination = Path(database)
    with tempfile.TemporaryDirectory(dir=destination.parent) as directory:
        snapshot = Path(directory) / "restore.sqlite"
        with snapshot.open("wb") as stream:
            shutil.copyfileobj(sys.stdin.buffer, stream)
        check(snapshot)
        os.replace(snapshot, destination)
else:
    raise SystemExit(f"Unknown action: {action}")
