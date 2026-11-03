import pytest
from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(str(tmp_path / "test.db"))
    return app.test_client()


GOOD = {"patient_name": "Nimal", "date": "2099-01-01", "time": "10:00", "status": "Booked"}


def test_create_and_list(client):
    assert client.post("/api/appointments", json=GOOD).status_code == 201
    assert len(client.get("/api/appointments").get_json()) == 1


def test_missing_name_rejected(client):
    r = client.post("/api/appointments", json={**GOOD, "patient_name": ""})
    assert r.status_code == 400


def test_past_date_rejected(client):
    r = client.post("/api/appointments", json={**GOOD, "date": "2000-01-01"})
    assert r.status_code == 400


def test_double_booking_blocked(client):
    client.post("/api/appointments", json=GOOD)
    r = client.post("/api/appointments", json={**GOOD, "patient_name": "Kamal"})
    assert r.status_code == 400


def test_update_and_delete(client):
    new_id = client.post("/api/appointments", json=GOOD).get_json()["id"]
    r = client.put(f"/api/appointments/{new_id}", json={**GOOD, "status": "Completed"})
    assert r.status_code == 200
    assert client.delete(f"/api/appointments/{new_id}").status_code == 204
    assert client.delete(f"/api/appointments/{new_id}").status_code == 404