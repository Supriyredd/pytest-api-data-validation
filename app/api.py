"""Demo pharmacy REST API (Flask + SQLite) used as the system under test."""
import os
import sqlite3

from flask import Flask, g, jsonify, request

API_TOKEN = os.environ.get("API_TOKEN", "local-dev-token")


def create_app(db_path: str) -> Flask:
    app = Flask(__name__)

    def db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(db_path)
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close(_exc):
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    @app.before_request
    def require_token():
        if request.path == "/health":
            return None
        if request.headers.get("Authorization") != f"Bearer {API_TOKEN}":
            return jsonify(error="unauthorized"), 401
        return None

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/patients")
    def patients():
        try:
            page = int(request.args.get("page", 1))
            size = int(request.args.get("size", 10))
        except ValueError:
            return jsonify(error="page and size must be integers"), 400
        if page < 1 or not 1 <= size <= 50:
            return jsonify(error="page must be >= 1 and size between 1 and 50"), 400
        total = db().execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        rows = db().execute(
            "SELECT id, mrn, first_name, last_name, birth_year FROM patients ORDER BY id LIMIT ? OFFSET ?",
            (size, (page - 1) * size),
        ).fetchall()
        return {"page": page, "size": size, "total": total, "items": [dict(r) for r in rows]}

    @app.get("/patients/<int:pid>/prescriptions")
    def prescriptions(pid: int):
        if not db().execute("SELECT 1 FROM patients WHERE id=?", (pid,)).fetchone():
            return jsonify(error="patient not found"), 404
        rows = db().execute(
            "SELECT id, drug_code, drug_name, quantity, refills_remaining, status "
            "FROM prescriptions WHERE patient_id=? ORDER BY id",
            (pid,),
        ).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.post("/prescriptions/<int:rx_id>/refill")
    def refill(rx_id: int):
        row = db().execute("SELECT refills_remaining, status FROM prescriptions WHERE id=?", (rx_id,)).fetchone()
        if not row:
            return jsonify(error="prescription not found"), 404
        if row["status"] == "CANCELLED":
            return jsonify(error="cancelled prescriptions cannot be refilled"), 409
        if row["refills_remaining"] == 0:
            return jsonify(error="no refills remaining"), 409
        db().execute(
            "UPDATE prescriptions SET refills_remaining = refills_remaining - 1, status='PENDING' WHERE id=?",
            (rx_id,),
        )
        db().commit()
        updated = db().execute("SELECT id, refills_remaining, status FROM prescriptions WHERE id=?", (rx_id,)).fetchone()
        return jsonify(dict(updated)), 200

    return app


if __name__ == "__main__":
    import tempfile

    from seed import seed

    path = os.path.join(tempfile.gettempdir(), "pharmacy_demo.db")
    with sqlite3.connect(path) as c:
        seed(c)
    create_app(path).run(port=int(os.environ.get("APP_PORT", 5001)))
