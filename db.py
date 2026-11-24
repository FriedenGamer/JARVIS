from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "jarvis.db"

VALID_STATUSES = {
    "pending",
    "approved",
    "rejected",
    "executing",
    "executed",
    "failed",
}


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tasks, audit_log, and records tables if they do not exist."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                args_json TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL,
                result_json TEXT,
                error_message TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                timestamp TEXT NOT NULL,
                event TEXT NOT NULL,
                details TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                data_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def log_event(task_id, event, details):
    """Append-only audit log writer; never updates or deletes rows."""
    init_db()
    now = _now_iso()
    details_str = details if isinstance(details, str) else json.dumps(details)
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO audit_log (task_id, timestamp, event, details)
            VALUES (?, ?, ?, ?)
            """,
            (task_id, now, str(event), details_str),
        )
        conn.commit()
        return cur.lastrowid


def create_task(tool_name, args, risk_level, reason, status="pending"):
    """Insert a new task row, log its creation, and return the new task id."""
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    init_db()
    now = _now_iso()
    args_str = args if isinstance(args, str) else json.dumps(args)
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks (
                timestamp, updated_at, tool_name, args_json,
                risk_level, reason, status, result_json, error_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL)
            """,
            (now, now, tool_name, args_str, risk_level, reason, status),
        )
        task_id = cur.lastrowid
        conn.commit()

    log_event(task_id, "task_created", f"tool={tool_name}, status={status}, reason={reason}")
    return task_id


def get_task(task_id):
    """Fetch a single task by id as a dict, or None if not found."""
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return dict(row) if row else None


def list_tasks(status=None):
    """Return all tasks, or filter by status if provided."""
    init_db()
    with _connect() as conn:
        if status is not None:
            if status not in VALID_STATUSES:
                raise ValueError(f"Invalid status: {status}")
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY id ASC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM tasks ORDER BY id ASC").fetchall()
        return [dict(r) for r in rows]


def set_status(task_id, status, result_json=None, error_message=None):
    """Update task status (and optional result or error) and append an audit entry."""
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    task = get_task(task_id)
    if task is None:
        raise ValueError(f"Task {task_id} not found")

    old_status = task["status"]
    now = _now_iso()
    res_str = (
        None
        if result_json is None
        else (result_json if isinstance(result_json, str) else json.dumps(result_json))
    )
    err_str = None if error_message is None else str(error_message)

    with _connect() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET status = ?, updated_at = ?, result_json = ?, error_message = ?
            WHERE id = ?
            """,
            (status, now, res_str, err_str, task_id),
        )
        conn.commit()

    log_event(
        task_id,
        "status_changed",
        json.dumps({"from": old_status, "to": status, "error": err_str}),
    )
    return get_task(task_id)


def update_task_payload(task_id, new_data):
    """Edit args_json only while status is pending; log both old and new values."""
    task = get_task(task_id)
    if task is None:
        raise ValueError(f"Task {task_id} not found")
    if task["status"] != "pending":
        raise ValueError(f"Cannot edit task {task_id} with status '{task['status']}'")

    old_args_str = task["args_json"]
    new_args_str = new_data if isinstance(new_data, str) else json.dumps(new_data)
    now = _now_iso()

    with _connect() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET args_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_args_str, now, task_id),
        )
        conn.commit()

    log_event(
        task_id,
        "task_edited",
        json.dumps({"old_args": old_args_str, "new_args": new_args_str}),
    )
    return get_task(task_id)


def approve_task(task_id):
    """Approve a task only when its current status is pending."""
    task = get_task(task_id)
    if task is None:
        raise ValueError(f"Task {task_id} not found")
    if task["status"] != "pending":
        raise ValueError(f"Cannot approve task {task_id} with status '{task['status']}'")
    return set_status(task_id, "approved")