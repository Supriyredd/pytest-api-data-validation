import pytest
from jsonschema import validate

from tests.schemas import PATIENT_PAGE, PRESCRIPTION

pytestmark = pytest.mark.api


def test_health_is_public(anon):
    r = anon.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.parametrize("path", ["/patients", "/patients/1/prescriptions"])
def test_endpoints_require_token(anon, path):
    r = anon.get(path)
    assert r.status_code == 401
    assert r.json()["error"] == "unauthorized"


def test_wrong_token_is_rejected(base_url):
    from qa_tools.client import PharmacyClient
    assert PharmacyClient(base_url, "not-the-token").get("/patients").status_code == 401


def test_patient_page_matches_schema(api):
    r = api.get("/patients", params={"page": 1, "size": 5})
    assert r.status_code == 200
    body = r.json()
    validate(body, PATIENT_PAGE)
    assert len(body["items"]) == 5


def test_pages_do_not_overlap(api):
    p1 = {p["id"] for p in api.get("/patients", params={"page": 1, "size": 10}).json()["items"]}
    p2 = {p["id"] for p in api.get("/patients", params={"page": 2, "size": 10}).json()["items"]}
    assert p1 and p2 and p1.isdisjoint(p2)


@pytest.mark.parametrize(
    "params",
    [{"page": 0}, {"size": 0}, {"size": 51}, {"page": "abc"}],
    ids=["page-zero", "size-zero", "size-too-big", "page-not-int"],
)
def test_invalid_paging_returns_400(api, params):
    r = api.get("/patients", params=params)
    assert r.status_code == 400
    assert "error" in r.json()


def test_prescriptions_match_schema(api):
    r = api.get("/patients/1/prescriptions")
    assert r.status_code == 200
    for rx in r.json():
        validate(rx, PRESCRIPTION)


def test_unknown_patient_returns_404(api):
    r = api.get("/patients/99999/prescriptions")
    assert r.status_code == 404
