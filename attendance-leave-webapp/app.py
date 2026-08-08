"""
Student Employee Attendance & Leave Management System — Web Edition
---------------------------------------------------------------------
Flask + SQLite. Run with:  python app.py
Then open http://127.0.0.1:5000 in a browser.
"""

import sqlite3
import os
from datetime import datetime, date

from flask import Flask, render_template, request, redirect, url_for, flash, g

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "attendance_leave.db")

LEAVE_TYPES = ["Sick", "Casual", "Emergency", "Other"]

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_FILE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id      TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            department      TEXT,
            hourly_wage     REAL DEFAULT 0,
            is_active       INTEGER DEFAULT 1,
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id      TEXT NOT NULL,
            work_date       TEXT NOT NULL,
            clock_in        TEXT,
            clock_out       TEXT,
            hours_worked    REAL,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id      TEXT NOT NULL,
            leave_type      TEXT NOT NULL,
            start_date      TEXT NOT NULL,
            end_date        TEXT NOT NULL,
            reason          TEXT,
            status          TEXT DEFAULT 'Pending',
            requested_at    TEXT DEFAULT (datetime('now')),
            decided_at      TEXT,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)
    conn.commit()
    conn.close()


def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    db = get_db()
    today = date.today().isoformat()

    students = db.execute(
        "SELECT * FROM students WHERE is_active = 1 ORDER BY name"
    ).fetchall()

    # Attach today's open/closed attendance status to each student
    student_rows = []
    for s in students:
        att = db.execute(
            "SELECT * FROM attendance WHERE student_id = ? AND work_date = ? "
            "ORDER BY id DESC LIMIT 1",
            (s["student_id"], today),
        ).fetchone()
        status = "not_started"
        if att and att["clock_in"] and not att["clock_out"]:
            status = "clocked_in"
        elif att and att["clock_out"]:
            status = "clocked_out"
        student_rows.append({"student": s, "status": status, "today": att})

    pending_count = db.execute(
        "SELECT COUNT(*) c FROM leave_requests WHERE status = 'Pending'"
    ).fetchone()["c"]

    active_count = len(students)
    clocked_in_count = sum(1 for r in student_rows if r["status"] == "clocked_in")

    return render_template(
        "dashboard.html",
        student_rows=student_rows,
        pending_count=pending_count,
        active_count=active_count,
        clocked_in_count=clocked_in_count,
        today=today,
    )


@app.route("/clock/<student_id>/<action>", methods=["POST"])
def clock(student_id, action):
    db = get_db()
    today = date.today().isoformat()
    now = datetime.now()

    if action == "in":
        open_row = db.execute(
            "SELECT * FROM attendance WHERE student_id = ? AND work_date = ? AND clock_out IS NULL",
            (student_id, today),
        ).fetchone()
        if open_row:
            flash(f"{student_id} is already clocked in.", "warning")
        else:
            db.execute(
                "INSERT INTO attendance (student_id, work_date, clock_in) VALUES (?, ?, ?)",
                (student_id, today, now.strftime("%H:%M:%S")),
            )
            db.commit()
            flash(f"{student_id} clocked in at {now.strftime('%H:%M')}.", "success")

    elif action == "out":
        row = db.execute(
            "SELECT * FROM attendance WHERE student_id = ? AND work_date = ? AND clock_out IS NULL",
            (student_id, today),
        ).fetchone()
        if not row:
            flash(f"No open clock-in found for {student_id} today.", "warning")
        else:
            clock_in_time = datetime.strptime(f"{today} {row['clock_in']}", "%Y-%m-%d %H:%M:%S")
            hours = round((now - clock_in_time).total_seconds() / 3600, 2)
            db.execute(
                "UPDATE attendance SET clock_out = ?, hours_worked = ? WHERE id = ?",
                (now.strftime("%H:%M:%S"), hours, row["id"]),
            )
            db.commit()
            flash(f"{student_id} clocked out. Hours worked: {hours}", "success")

    return redirect(url_for("dashboard"))


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------

@app.route("/students", methods=["GET", "POST"])
def students():
    db = get_db()

    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        name = request.form.get("name", "").strip()
        department = request.form.get("department", "").strip()
        wage = request.form.get("hourly_wage", "0").strip() or "0"

        existing = db.execute(
            "SELECT 1 FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()

        if not student_id or not name:
            flash("Student ID and name are required.", "warning")
        elif existing:
            flash(f"A student with ID '{student_id}' already exists.", "warning")
        else:
            try:
                wage_val = float(wage)
            except ValueError:
                wage_val = 0.0
            db.execute(
                "INSERT INTO students (student_id, name, department, hourly_wage) VALUES (?, ?, ?, ?)",
                (student_id, name, department, wage_val),
            )
            db.commit()
            flash(f"Added {name} ({student_id}).", "success")
        return redirect(url_for("students"))

    all_students = db.execute("SELECT * FROM students ORDER BY is_active DESC, name").fetchall()
    return render_template("students.html", students=all_students)


@app.route("/students/<student_id>/toggle", methods=["POST"])
def toggle_student(student_id):
    db = get_db()
    row = db.execute("SELECT is_active FROM students WHERE student_id = ?", (student_id,)).fetchone()
    if row:
        new_status = 0 if row["is_active"] else 1
        db.execute("UPDATE students SET is_active = ? WHERE student_id = ?", (new_status, student_id))
        db.commit()
        flash(("Reactivated " if new_status else "Deactivated ") + student_id, "success")
    return redirect(url_for("students"))


# ---------------------------------------------------------------------------
# Attendance log
# ---------------------------------------------------------------------------

@app.route("/attendance")
def attendance():
    db = get_db()
    student_id = request.args.get("student_id", "").strip()

    if student_id:
        rows = db.execute(
            "SELECT * FROM attendance WHERE student_id = ? ORDER BY work_date DESC, id DESC",
            (student_id,),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM attendance ORDER BY work_date DESC, id DESC LIMIT 200"
        ).fetchall()

    all_students = db.execute("SELECT student_id, name FROM students ORDER BY name").fetchall()
    return render_template(
        "attendance.html", rows=rows, all_students=all_students, selected=student_id
    )


# ---------------------------------------------------------------------------
# Leave requests
# ---------------------------------------------------------------------------

@app.route("/leave", methods=["GET", "POST"])
def leave():
    db = get_db()

    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        leave_type = request.form.get("leave_type", "")
        start = request.form.get("start_date", "")
        end = request.form.get("end_date", "")
        reason = request.form.get("reason", "").strip()

        exists = db.execute(
            "SELECT 1 FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()

        if not exists:
            flash("No such student ID.", "warning")
        elif leave_type not in LEAVE_TYPES:
            flash("Invalid leave type.", "warning")
        else:
            try:
                s, e = parse_date(start), parse_date(end)
                if e < s:
                    flash("End date cannot be before start date.", "warning")
                else:
                    db.execute(
                        "INSERT INTO leave_requests (student_id, leave_type, start_date, end_date, reason) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (student_id, leave_type, start, end, reason),
                    )
                    db.commit()
                    flash("Leave request submitted.", "success")
            except ValueError:
                flash("Invalid date format.", "warning")

        return redirect(url_for("leave"))

    all_requests = db.execute(
        "SELECT * FROM leave_requests ORDER BY "
        "CASE status WHEN 'Pending' THEN 0 ELSE 1 END, requested_at DESC"
    ).fetchall()
    all_students = db.execute("SELECT student_id, name FROM students WHERE is_active = 1 ORDER BY name").fetchall()

    return render_template(
        "leave.html", requests=all_requests, leave_types=LEAVE_TYPES, all_students=all_students
    )


@app.route("/leave/<int:req_id>/<decision>", methods=["POST"])
def decide_leave(req_id, decision):
    db = get_db()
    if decision in ("approve", "reject"):
        status = "Approved" if decision == "approve" else "Rejected"
        db.execute(
            "UPDATE leave_requests SET status = ?, decided_at = datetime('now') WHERE id = ?",
            (status, req_id),
        )
        db.commit()
        flash(f"Request #{req_id} {status.lower()}.", "success")
    return redirect(url_for("leave"))


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@app.route("/reports")
def reports():
    db = get_db()
    student_id = request.args.get("student_id", "")
    month = request.args.get("month", date.today().strftime("%Y-%m"))

    attendance_summary = None
    leave_summary = None

    if student_id:
        rows = db.execute(
            "SELECT * FROM attendance WHERE student_id = ? AND work_date LIKE ? ORDER BY work_date",
            (student_id, f"{month}%"),
        ).fetchall()
        total_hours = sum(r["hours_worked"] or 0 for r in rows)
        attendance_summary = {
            "days_present": len(rows),
            "total_hours": round(total_hours, 2),
            "rows": rows,
        }

        leave_rows = db.execute(
            "SELECT * FROM leave_requests WHERE student_id = ?", (student_id,)
        ).fetchall()
        approved_days = 0
        counts = {}
        for r in leave_rows:
            counts[r["leave_type"]] = counts.get(r["leave_type"], 0) + 1
            if r["status"] == "Approved":
                approved_days += (parse_date(r["end_date"]) - parse_date(r["start_date"])).days + 1
        leave_summary = {"approved_days": approved_days, "counts": counts}

    all_students = db.execute("SELECT student_id, name FROM students ORDER BY name").fetchall()
    return render_template(
        "reports.html",
        all_students=all_students,
        selected=student_id,
        month=month,
        attendance_summary=attendance_summary,
        leave_summary=leave_summary,
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
