# Student Employee Attendance & Leave — Web App

## Setup

```bash
pip install flask
python app.py
```

Then open http://127.0.0.1:5000 in your browser.

A local SQLite file `attendance_leave.db` is created automatically on first run.

## Pages

- **Dashboard** — see every active employee's status today, clock them in/out with one click
- **Employees** — add new student employees, deactivate/reactivate existing ones
- **Attendance Log** — full history, filterable by employee
- **Leave Requests** — submit requests, approve/reject pending ones
- **Reports** — monthly attendance totals and leave usage per employee

## Notes

- No login system yet — anyone with access to the page can act as admin/supervisor. Add authentication (e.g. Flask-Login) before deploying somewhere multiple people can reach it.
- `app.secret_key` in `app.py` is a placeholder — change it before any real deployment.
- Data lives in `attendance_leave.db` in the same folder; delete it to reset everything.
