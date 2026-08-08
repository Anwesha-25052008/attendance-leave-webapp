# Build & Run Script — Student Employee Attendance & Leave Management System

## Project
Flask + SQLite web application for tracking student employee attendance and leave requests.

## Prerequisites
- Python 3.9+ (tested with Python 3.11)
- pip

## 1. Get the code
```bash
git clone https://github.com/Anwesha-25052008/attendance-leave-webapp.git
cd attendance-leave-webapp
```
(Or unzip the submitted project folder and `cd` into it.)

## 2. Create a virtual environment (recommended)
```bash
python -m venv venv

# Activate it
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS / Linux
```

## 3. Install dependencies
```bash
pip install flask
```
No `requirements.txt` is needed beyond Flask — all other modules used (`sqlite3`, `os`, `datetime`) are part of the Python standard library.

## 4. Run the build (initialize & start the app)
```bash
python app.py
```
On first run, Flask/SQLite automatically creates `attendance_leave.db` in the project folder and sets up the required tables (`students`, `attendance`, `leave_requests`, etc.). No separate migration step is required.

## 5. Access the application
Open a browser and go to:
```
http://127.0.0.1:5000
```

## Available pages
| Route         | Purpose                                              |
|---------------|-------------------------------------------------------|
| Dashboard     | View today's status for all active employees; clock in/out |
| Students      | Add new student employees; activate/deactivate existing ones |
| Attendance    | Full attendance history, filterable by employee       |
| Leave         | Submit leave requests; approve/reject pending requests |
| Reports       | Monthly attendance totals and leave usage per employee |

## Notes for reviewers
- There is currently **no authentication** — anyone with the URL can act as admin.
- `app.secret_key` in `app.py` is a placeholder (`"dev-secret-key-change-in-production"`) and should be changed before any real deployment.
- All data is stored in `attendance_leave.db`. Delete this file to reset the app to a clean state.
- To stop the server, press `Ctrl+C` in the terminal running `python app.py`.

## Troubleshooting
- **`ModuleNotFoundError: No module named 'flask'`** → run `pip install flask` in the active virtual environment.
- **Port 5000 already in use** → edit the bottom of `app.py` where `app.run(...)` is called and change the port, e.g. `app.run(debug=True, port=5050)`.
- **Database looks stale/corrupted** → close the app, delete `attendance_leave.db`, and restart with `python app.py` to regenerate it.
