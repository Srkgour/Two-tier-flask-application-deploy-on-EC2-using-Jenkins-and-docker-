import os
import time

import psycopg2
from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)
_db_ready = False


def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        dbname=os.getenv("DB_NAME", "appdb"),
        user=os.getenv("DB_USER", "appuser"),
        password=os.getenv("DB_PASSWORD", ""),
        connect_timeout=3,
    )


def ensure_db():
    """Create the table once, retrying while the database container starts."""
    global _db_ready
    if _db_ready:
        return
    for attempt in range(10):
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS tasks ("
                    "id SERIAL PRIMARY KEY, title TEXT NOT NULL, "
                    "created_at TIMESTAMP DEFAULT NOW())"
                )
            _db_ready = True
            return
        except psycopg2.OperationalError:
            time.sleep(2)
    raise RuntimeError("Database is not reachable")


def list_tasks():
    ensure_db()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, title FROM tasks ORDER BY id DESC")
        return cur.fetchall()


@app.route("/")
def index():
    return render_template(
        "index.html",
        tasks=list_tasks(),
        version=os.getenv("APP_VERSION", "local"),
        host=os.getenv("HOSTNAME", "unknown"),
    )


@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title", "").strip()
    if title:
        ensure_db()
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO tasks (title) VALUES (%s)", (title[:200],))
    return redirect(url_for("index"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    ensure_db()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    return redirect(url_for("index"))


@app.route("/api/tasks")
def api_tasks():
    return jsonify([{"id": i, "title": t} for i, t in list_tasks()])


@app.route("/health")
def health():
    return jsonify(status="ok", version=os.getenv("APP_VERSION", "local"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
