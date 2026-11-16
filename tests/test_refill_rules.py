"""Business-rule tests: each test picks its own data from the DB so it never depends on another test."""
import pytest

from tests.conftest import query

pytestmark = pytest.mark.api


def first(db, where):
    rows = query(db, f"SELECT id, refills_remaining, status FROM prescriptions WHERE {where} ORDER BY id LIMIT 1")
    if not rows:
        pytest.skip(f"no seed data for: {where}")
    return rows[0]


def test_refill_decrements_and_persists(api, db):
    rx = first(db, "refills_remaining > 0 AND status != 'CANCELLED'")
    r = api.post(f"/prescriptions/{rx['id']}/refill")
    assert r.status_code == 200
    assert r.json() == {"id": rx["id"], "refills_remaining": rx["refills_remaining"] - 1, "status": "PENDING"}
    # Verify the database, not just the response.
    stored = query(db, "SELECT refills_remaining, status FROM prescriptions WHERE id=?", (rx["id"],))[0]
    assert stored == {"refills_remaining": rx["refills_remaining"] - 1, "status": "PENDING"}


def test_no_refills_left_is_409(api, db):
    rx = first(db, "refills_remaining = 0 AND status != 'CANCELLED'")
    r = api.post(f"/prescriptions/{rx['id']}/refill")
    assert r.status_code == 409
    assert r.json()["error"] == "no refills remaining"


def test_cancelled_prescription_is_409(api, db):
    rx = first(db, "status = 'CANCELLED'")
    before = rx["refills_remaining"]
    r = api.post(f"/prescriptions/{rx['id']}/refill")
    assert r.status_code == 409
    assert query(db, "SELECT refills_remaining FROM prescriptions WHERE id=?", (rx["id"],))[0]["refills_remaining"] == before


def test_unknown_prescription_is_404(api):
    assert api.post("/prescriptions/999999/refill").status_code == 404
