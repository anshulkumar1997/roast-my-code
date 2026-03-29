"""
Integration tests for the /api/roast endpoint.
We mock the AI service so tests are fast and don't cost money.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

MOCK_ROAST = {
    "roast": "This code looks like it was written during a power outage.",
    "feedback": "Consider using list comprehensions and adding type hints.",
    "rating": 4,
}


@pytest.fixture(autouse=True)
def mock_roaster():
    """Patch the AI service for every test — no real API calls."""
    with patch("app.routers.roast.roast_code", new_callable=AsyncMock) as mock:
        mock.return_value = MOCK_ROAST
        yield mock


# ─── Happy path ───────────────────────────────────────────────────────────────


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_roast_returns_expected_shape():
    res = client.post("/api/roast", json={"code": "print('hello world')", "language": "python"})
    assert res.status_code == 200
    body = res.json()
    assert "roast" in body
    assert "feedback" in body
    assert isinstance(body["rating"], int)
    assert 1 <= body["rating"] <= 10


def test_roast_default_language():
    """language field should default to 'auto' and still work."""
    res = client.post("/api/roast", json={"code": "let x = 1"})
    assert res.status_code == 200


# ─── Validation errors ────────────────────────────────────────────────────────


def test_roast_rejects_empty_code():
    res = client.post("/api/roast", json={"code": "   "})
    assert res.status_code == 422


def test_roast_rejects_missing_code():
    res = client.post("/api/roast", json={})
    assert res.status_code == 422


def test_roast_rejects_code_too_long():
    res = client.post("/api/roast", json={"code": "x" * 5001})
    assert res.status_code == 422
