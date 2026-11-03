import sqlite3
from datetime import datetime
from flask import Flask, jsonify, request, g

STATUSES = ["Booked", "Completed", "Cancelled"]


def create_app(db_path="appointments.db"):
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config["DB_PATH"] = db_path

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_):
        db = g.pop("db", None)
        if db:
            db.close()

    with app.app_context():
        get_db().execute(
            """CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Booked',
                notes TEXT DEFAULT ''
            )"""
        )
        get_db().commit()

    def validate(data, appt_id=-1):
        errors = []
        name = (data.get("patient_name") or "").strip()
        date = data.get("date") or ""
        time = data.get("time") or ""
        status = data.get("status") or "Booked"

        if not name:
            errors.append("Patient name is required.")
        try:
            when = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
            when = None
            errors.append("A valid date (YYYY-MM-DD) and time (HH:MM) are required.")
        if status not in STATUSES:
            errors.append(f"Status must be one of {STATUSES}.")

        if when and status == "Booked":
            if when < datetime.now():
                errors.append("Cannot book an appointment in the past.")
            clash = get_db().execute(
                "SELECT id FROM appointments WHERE date=? AND time=? AND status='Booked' AND id != ?",
                (date, time, appt_id),
            ).fetchone()
            if clash:
                errors.append("That time slot is already booked.")
        return errors, {
            "patient_name": name,
            "date": date,
            "time": time,
            "status": status,
            "notes": (data.get("notes") or "").strip(),
        }

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/api/appointments")
    def list_appointments():
        sql, params = "SELECT * FROM appointments WHERE 1=1", []
        if request.args.get("status"):
            sql += " AND status=?"
            params.append(request.args["status"])
        if request.args.get("date"):
            sql += " AND date=?"
            params.append(request.args["date"])
        if request.args.get("q"):
            sql += " AND patient_name LIKE ?"
            params.append(f"%{request.args['q']}%")
        sql += " ORDER BY date, time"
        rows = get_db().execute(sql, params).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.post("/api/appointments")
    def create_appointment():
        errors, clean = validate(request.get_json(silent=True) or {})
        if errors:
            return jsonify({"errors": errors}), 400
        db = get_db()
        cur = db.execute(
            "INSERT INTO appointments (patient_name, date, time, status, notes) VALUES (?,?,?,?,?)",
            (clean["patient_name"], clean["date"], clean["time"], clean["status"], clean["notes"]),
        )
        db.commit()
        return jsonify({"id": cur.lastrowid, **clean}), 201

    @app.put("/api/appointments/<int:appt_id>")
    def update_appointment(appt_id):
        db = get_db()
        if not db.execute("SELECT id FROM appointments WHERE id=?", (appt_id,)).fetchone():
            return jsonify({"errors": ["Appointment not found."]}), 404
        errors, clean = validate(request.get_json(silent=True) or {}, appt_id)
        if errors:
            return jsonify({"errors": errors}), 400
        db.execute(
            "UPDATE appointments SET patient_name=?, date=?, time=?, status=?, notes=? WHERE id=?",
            (clean["patient_name"], clean["date"], clean["time"], clean["status"], clean["notes"], appt_id),
        )
        db.commit()
        return jsonify({"id": appt_id, **clean})

    @app.delete("/api/appointments/<int:appt_id>")
    def delete_appointment(appt_id):
        db = get_db()
        cur = db.execute("DELETE FROM appointments WHERE id=?", (appt_id,))
        db.commit()
        if cur.rowcount == 0:
            return jsonify({"errors": ["Appointment not found."]}), 404
        return "", 204

    return app


if __name__ == "__main__":
    create_app().run(debug=True, use_reloader=False)