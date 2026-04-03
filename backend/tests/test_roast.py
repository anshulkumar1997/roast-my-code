"""
Integration tests for the /api/roast endpoint.
We mock the AI service and Redis so tests are fast, free, and self-contained.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.services.auth import create_access_token

client = TestClient(app)


MOCK_ROAST = {
    "roast": "This code looks like it was written during a power outage.",
    "feedback": "Consider using list comprehensions and adding type hints.",
    "rating": 4,
}

# A real-looking JWT for a test user — signed with the app's secret
# ── Test user + token ─────────────────────────────────────────────
TEST_EMAIL = "test@example.com"
TEST_TOKEN = create_access_token({"sub": TEST_EMAIL})
AUTH_HEADERS = {"Authorization": f"Bearer {TEST_TOKEN}"}
TEST_USER = {"email": TEST_EMAIL, "is_active": True}


# ── Fixtures ──────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def mock_roaster():
    """Patch AI service — no real API calls."""
    with patch("app.routers.roast.roast_code", new_callable=AsyncMock) as mock:
        mock.return_value = MOCK_ROAST
        yield mock


@pytest.fixture(autouse=True)
def mock_rate_limit():
    """Patch Redis rate limiter — never rate limit in tests."""
    with patch("app.routers.roast.check_rate_limit", new_callable=AsyncMock) as mock:
        mock.return_value = 9
        yield mock


@pytest.fixture(autouse=True)
def mock_get_user_email():
    """Patch email extractor used by rate limiter in roast route."""
    with patch("app.routers.roast.get_user_email_from_request", return_value=TEST_EMAIL):
        yield


# ── DB override ───────────────────────────────────────────────────
# FastAPI dependency injection — swap get_db for a fake in all tests
def get_mock_db():
    """Returns a fake MongoDB that returns TEST_USER for any find_one call."""
    mock_collection = AsyncMock()
    mock_collection.find_one = AsyncMock(return_value=TEST_USER)
    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(return_value=mock_collection)
    return mock_db


app.dependency_overrides[get_db] = get_mock_db

client = TestClient(app)


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
