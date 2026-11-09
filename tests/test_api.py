from fastapi.testclient import TestClient

from wwe_data.api.app import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_overview_and_events():
    r = client.get("/api/analytics/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["kpis"]["total_events"] > 0
    assert body["kpis"]["total_matches"] > 0

    r = client.get("/api/events", params={"year": 2000, "limit": 5})
    assert r.status_code == 200
    assert len(r.json()["items"]) <= 5


def test_mitb_endpoint():
    r = client.get("/api/analytics/money-in-the-bank")
    assert r.status_code == 200
    assert "rows" in r.json()
