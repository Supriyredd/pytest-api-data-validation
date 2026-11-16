"""API-to-database reconciliation: the API must expose exactly what the database holds."""
import pytest

from qa_tools.reconcile import reconcile, write_report
from tests.conftest import query

pytestmark = pytest.mark.data

PATIENT_COLS = ["mrn", "first_name", "last_name", "birth_year"]
RX_COLS = ["drug_code", "drug_name", "quantity", "refills_remaining", "status"]


def test_all_patients_reconcile(api, db):
    api_rows = api.all_patients(size=7)  # odd page size exercises the last partial page
    db_rows = query(db, "SELECT id, mrn, first_name, last_name, birth_year FROM patients")
    diff = reconcile(api_rows, db_rows, key="id", columns=PATIENT_COLS)
    write_report(diff, "reports/patient_reconciliation.csv")
    assert diff.empty, f"{len(diff)} mismatches, see reports/patient_reconciliation.csv\n{diff.head(10)}"


def test_prescriptions_reconcile_for_every_patient(api, db):
    api_rows, db_rows = [], []
    for p in query(db, "SELECT id FROM patients"):
        api_rows += api.get(f"/patients/{p['id']}/prescriptions").json()
        db_rows += query(db, "SELECT id, drug_code, drug_name, quantity, refills_remaining, status "
                             "FROM prescriptions WHERE patient_id=?", (p["id"],))
    diff = reconcile(api_rows, db_rows, key="id", columns=RX_COLS)
    write_report(diff, "reports/prescription_reconciliation.csv")
    assert diff.empty, diff.head(10)


def test_reconcile_detects_mismatches():
    """The checker itself is tested: it must catch a changed value and a missing row."""
    api_rows = [{"id": 1, "v": "a"}, {"id": 2, "v": "b"}]
    db_rows = [{"id": 1, "v": "a"}, {"id": 2, "v": "X"}, {"id": 3, "v": "c"}]
    diff = reconcile(api_rows, db_rows, key="id", columns=["v"])
    assert diff.to_dict("records") == [
        {"id": 2, "column": "v", "api": "b", "db": "X"},
        {"id": 3, "column": "*", "api": "missing", "db": "present"},
    ]


def test_data_quality_rules(db):
    """Checks that should hold for any extract: unique keys, no orphans, valid ranges."""
    assert query(db, "SELECT mrn FROM patients GROUP BY mrn HAVING COUNT(*) > 1") == []
    assert query(db, "SELECT p.id FROM prescriptions p LEFT JOIN patients pt ON pt.id = p.patient_id WHERE pt.id IS NULL") == []
    assert query(db, "SELECT id FROM prescriptions WHERE quantity <= 0 OR refills_remaining < 0") == []
