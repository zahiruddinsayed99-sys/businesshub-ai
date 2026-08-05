from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_healthz_endpoint():
    response = client.get("/api/v1/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app_name"] == "BusinessHub AI"
