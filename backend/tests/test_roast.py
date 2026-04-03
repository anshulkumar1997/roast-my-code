"""
Integration tests for the /api/roast endpoint.
We mock the AI service and Redis so tests are fast, free, and self-contained.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth import create_access_token

client = TestClient(app)


MOCK_ROAST = {
    "roast": "This code looks like it was written during a power outage.",
    "feedback": "Consider using list comprehensions and adding type hints.",
    "rating": 4,
}

# A real-looking JWT for a test user — signed with the app's secret
TEST_EMAIL = "test@example.com"
TEST_TOKEN = create_access_token({"sub": TEST_EMAIL})
AUTH_HEADERS = {"Authorization": f"Bearer {TEST_TOKEN}"}


@pytest.fixture(autouse=True)
def mock_roaster():
    """Patch the AI service for every test — no real API calls."""
    with patch("app.routers.roast.roast_code", new_callable=AsyncMock) as mock:
        mock.return_value = MOCK_ROAST
        yield mock


@pytest.fixture(autouse=True)
def mock_redis():
    """
    Patch Redis so tests don't need a real Redis instance.
    check_rate_limit is mocked to do nothing (never rate limit in tests).
    """
    with patch("app.routers.roast.check_rate_limit", new_callable=AsyncMock) as mock:
        mock.return_value = 9  # 9 remaining requests
        yield mock


@pytest.fixture(autouse=True)
def mock_db():
    """
    Patch MongoDB so get_current_user can find our test user.
    Without this, auth middleware would hit a real DB and fail.
    """
    test_user = {"email": TEST_EMAIL, "is_active": True}
    mock_collection = AsyncMock()
    mock_collection.find_one = AsyncMock(return_value=test_user)

    mock_db_instance = MagicMock()
    mock_db_instance.__getitem__ = MagicMock(return_value=mock_collection)

    with patch("app.middleware.auth.get_db", return_value=iter([mock_db_instance])):
        yield mock_db_instance


# ─── Happy path ───────────────────────────────────────────────────────────────


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_roast_returns_expected_shape():
    res = client.post(
        "/api/roast",
        json={"code": "print('hello world')", "language": "python"},
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 200
    body = res.json()
    assert "roast" in body
    assert "feedback" in body
    assert isinstance(body["rating"], int)
    assert 1 <= body["rating"] <= 10


def test_roast_default_language():
    res = client.post(
        "/api/roast",
        json={"code": "let x = 1"},
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 200


def test_roast_requires_auth():
    """No token → 403 Forbidden."""
    res = client.post("/api/roast", json={"code": "print('hello')"})
    assert res.status_code == 403


# ─── Validation errors ────────────────────────────────────────────────────────


def test_roast_rejects_empty_code():
    res = client.post("/api/roast", json={"code": "   "}, headers=AUTH_HEADERS)
    assert res.status_code == 422


def test_roast_rejects_missing_code():
    res = client.post("/api/roast", json={}, headers=AUTH_HEADERS)
    assert res.status_code == 422


def test_roast_rejects_code_too_long():
    res = client.post("/api/roast", json={"code": "x" * 5001}, headers=AUTH_HEADERS)
    assert res.status_code == 422
