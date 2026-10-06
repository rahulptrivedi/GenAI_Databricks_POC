from fastapi.testclient import TestClient

from app.api.application import create_app
from app.core.config import Settings
from app.models.chat import ExecutionStatus


def test_health_and_unconfigured_chat_contract() -> None:
    client = TestClient(create_app(settings=Settings()))

    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").status_code == 503
    response = client.post("/api/chat", json={"question": "Monthly revenue?"})

    assert response.status_code == 200
    assert response.json()["status"] == ExecutionStatus.NOT_CONFIGURED
    assert response.json()["sources"] == []


def test_ui_and_assets_are_served_from_same_origin() -> None:
    client = TestClient(create_app(settings=Settings()))

    assert "Catalog Desk" in client.get("/").text
    assert client.get("/static/chat.js").status_code == 200
    assert client.get("/static/../../.env.example").status_code == 404


def test_feedback_accepts_only_minimal_rating_metadata() -> None:
    client = TestClient(create_app(settings=Settings()))
    response = client.post(
        "/api/feedback",
        json={"correlation_id": "00000000-0000-4000-8000-000000000000", "rating": "helpful"},
    )

    assert response.status_code == 202
    assert response.json() == {"status": "accepted"}
