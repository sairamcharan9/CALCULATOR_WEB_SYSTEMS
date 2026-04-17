"""
Integration Tests — BREAD Endpoints for Calculations
=====================================================

Covers all five BREAD operations (Browse, Read, Edit, Add, Delete) using FastAPI's
TestClient with an in-memory SQLite override.

Positive scenarios: successful CRUD flows.
Negative scenarios: 401 (unauthenticated), 403 (wrong owner), 404 (not found), 422 (invalid input).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.api.database import Base, get_db
from app.api.security import create_access_token

# ── In-memory test database ────────────────────────────────────────────────

TEST_DB_URL = "sqlite://"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_db():
    """Recreate tables before each test and drop after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def user_a():
    """Register user A via API and return (user_dict, jwt_headers)."""
    resp = client.post("/users/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "AlicePass123!",
    })
    assert resp.status_code == 201, resp.text
    user = resp.json()
    token = create_access_token({"sub": str(user["id"])})
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


@pytest.fixture
def user_b():
    """Register a second user B."""
    resp = client.post("/users/register", json={
        "username": "bob",
        "email": "bob@example.com",
        "password": "BobPass456!",
    })
    assert resp.status_code == 201, resp.text
    user = resp.json()
    token = create_access_token({"sub": str(user["id"])})
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


@pytest.fixture
def saved_calc(user_a):
    """Create one calculation for user_a and return the calculation dict."""
    _user, headers = user_a
    resp = client.post(
        "/calculations/",
        json={"a": 10.0, "b": 5.0, "type": "ADD"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Positive Scenarios ────────────────────────────────────────────────────

class TestBrowse:
    """GET /calculations/ — list all calculations for the logged-in user."""

    def test_browse_returns_empty_list(self, user_a):
        _user, headers = user_a
        resp = client.get("/calculations/", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_browse_returns_own_calculations(self, user_a, saved_calc):
        _user, headers = user_a
        resp = client.get("/calculations/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == saved_calc["id"]

    def test_browse_does_not_return_other_users_calculations(self, user_a, user_b, saved_calc):
        """User B should see an empty list even though User A has a record."""
        _user_b, headers_b = user_b
        resp = client.get("/calculations/", headers=headers_b)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_browse_requires_auth(self):
        resp = client.get("/calculations/")
        assert resp.status_code == 401


class TestRead:
    """GET /calculations/{id} — fetch a single calculation."""

    def test_read_own_calculation(self, user_a, saved_calc):
        _user, headers = user_a
        resp = client.get(f"/calculations/{saved_calc['id']}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == saved_calc["id"]
        assert data["result"] == 15.0
        assert data["type"] == "ADD"

    def test_read_nonexistent_returns_404(self, user_a):
        _user, headers = user_a
        resp = client.get("/calculations/99999", headers=headers)
        assert resp.status_code == 404

    def test_read_other_users_calculation_returns_403(self, user_a, user_b, saved_calc):
        _user_b, headers_b = user_b
        resp = client.get(f"/calculations/{saved_calc['id']}", headers=headers_b)
        assert resp.status_code == 403

    def test_read_requires_auth(self, saved_calc):
        resp = client.get(f"/calculations/{saved_calc['id']}")
        assert resp.status_code == 401


class TestAdd:
    """POST /calculations/ — create a new calculation."""

    def test_add_addition(self, user_a):
        _user, headers = user_a
        resp = client.post(
            "/calculations/",
            json={"a": 7.0, "b": 3.0, "type": "ADD"},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["result"] == 10.0
        assert data["type"] == "ADD"

    def test_add_subtraction(self, user_a):
        _user, headers = user_a
        resp = client.post(
            "/calculations/",
            json={"a": 20.0, "b": 8.0, "type": "SUBTRACT"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["result"] == 12.0

    def test_add_multiplication(self, user_a):
        _user, headers = user_a
        resp = client.post(
            "/calculations/",
            json={"a": 4.0, "b": 6.0, "type": "MULTIPLY"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["result"] == 24.0

    def test_add_division(self, user_a):
        _user, headers = user_a
        resp = client.post(
            "/calculations/",
            json={"a": 15.0, "b": 3.0, "type": "DIVIDE"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["result"] == 5.0

    def test_add_int_divide(self, user_a):
        _user, headers = user_a
        resp = client.post(
            "/calculations/",
            json={"a": 10.0, "b": 3.0, "type": "INT_DIVIDE"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["result"] == 3.0

    def test_add_user_id_in_response_matches_token(self, user_a):
        user, headers = user_a
        resp = client.post(
            "/calculations/",
            json={"a": 1.0, "b": 1.0, "type": "ADD"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["user_id"] == user["id"]

    def test_add_divide_by_zero_returns_422(self, user_a):
        _user, headers = user_a
        resp = client.post(
            "/calculations/",
            json={"a": 10.0, "b": 0.0, "type": "DIVIDE"},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_add_invalid_operation_returns_422(self, user_a):
        _user, headers = user_a
        resp = client.post(
            "/calculations/",
            json={"a": 10.0, "b": 2.0, "type": "POWER"},  # not in OperationType enum
            headers=headers,
        )
        assert resp.status_code == 422

    def test_add_requires_auth(self):
        resp = client.post(
            "/calculations/",
            json={"a": 5.0, "b": 2.0, "type": "ADD"},
        )
        assert resp.status_code == 401


class TestEdit:
    """PUT /calculations/{id} — fully update an existing calculation."""

    def test_edit_updates_values(self, user_a, saved_calc):
        _user, headers = user_a
        resp = client.put(
            f"/calculations/{saved_calc['id']}",
            json={"a": 100.0, "b": 25.0, "type": "MULTIPLY"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"] == 2500.0
        assert data["type"] == "MULTIPLY"

    def test_edit_persists_in_db(self, user_a, saved_calc):
        """Subsequent read should reflect the updated values."""
        _user, headers = user_a
        client.put(
            f"/calculations/{saved_calc['id']}",
            json={"a": 3.0, "b": 3.0, "type": "MULTIPLY"},
            headers=headers,
        )
        read_resp = client.get(f"/calculations/{saved_calc['id']}", headers=headers)
        assert read_resp.json()["result"] == 9.0

    def test_edit_nonexistent_returns_404(self, user_a):
        _user, headers = user_a
        resp = client.put(
            "/calculations/99999",
            json={"a": 1.0, "b": 1.0, "type": "ADD"},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_edit_other_users_calculation_returns_403(self, user_a, user_b, saved_calc):
        _user_b, headers_b = user_b
        resp = client.put(
            f"/calculations/{saved_calc['id']}",
            json={"a": 1.0, "b": 1.0, "type": "ADD"},
            headers=headers_b,
        )
        assert resp.status_code == 403

    def test_edit_divide_by_zero_returns_422(self, user_a, saved_calc):
        _user, headers = user_a
        resp = client.put(
            f"/calculations/{saved_calc['id']}",
            json={"a": 10.0, "b": 0.0, "type": "DIVIDE"},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_edit_requires_auth(self, saved_calc):
        resp = client.put(
            f"/calculations/{saved_calc['id']}",
            json={"a": 1.0, "b": 1.0, "type": "ADD"},
        )
        assert resp.status_code == 401


class TestDelete:
    """DELETE /calculations/{id} — remove a calculation."""

    def test_delete_own_calculation(self, user_a, saved_calc):
        _user, headers = user_a
        resp = client.delete(f"/calculations/{saved_calc['id']}", headers=headers)
        assert resp.status_code == 204

    def test_deleted_calculation_no_longer_exists(self, user_a, saved_calc):
        _user, headers = user_a
        client.delete(f"/calculations/{saved_calc['id']}", headers=headers)
        read_resp = client.get(f"/calculations/{saved_calc['id']}", headers=headers)
        assert read_resp.status_code == 404

    def test_delete_does_not_affect_other_records(self, user_a):
        """Deleting one record must not remove others."""
        _user, headers = user_a
        r1 = client.post("/calculations/", json={"a": 1.0, "b": 1.0, "type": "ADD"}, headers=headers)
        r2 = client.post("/calculations/", json={"a": 2.0, "b": 2.0, "type": "ADD"}, headers=headers)
        client.delete(f"/calculations/{r1.json()['id']}", headers=headers)
        browse = client.get("/calculations/", headers=headers)
        ids = [c["id"] for c in browse.json()]
        assert r1.json()["id"] not in ids
        assert r2.json()["id"] in ids

    def test_delete_nonexistent_returns_404(self, user_a):
        _user, headers = user_a
        resp = client.delete("/calculations/99999", headers=headers)
        assert resp.status_code == 404

    def test_delete_other_users_calculation_returns_403(self, user_a, user_b, saved_calc):
        _user_b, headers_b = user_b
        resp = client.delete(f"/calculations/{saved_calc['id']}", headers=headers_b)
        assert resp.status_code == 403

    def test_delete_requires_auth(self, saved_calc):
        resp = client.delete(f"/calculations/{saved_calc['id']}")
        assert resp.status_code == 401
