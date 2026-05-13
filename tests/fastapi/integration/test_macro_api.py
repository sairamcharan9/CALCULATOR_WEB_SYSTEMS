"""
Integration Tests — Dynamic User-Defined Formula Macros API
===========================================================

Covers macro creation, listing, recursive dynamic execution server-side,
and deletion via authenticated TestClient.
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


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    """Recreate tables before each test and drop after."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


@pytest.fixture
def macro_user_a():
    """Register User A and return (user_dict, headers)."""
    resp = client.post("/users/register", json={
        "username": "macro_alice",
        "email": "macro_alice@example.com",
        "password": "MacroPass123!",
    })
    if resp.status_code == 409:
        # User already exists in persistent or testing DB, authenticate directly
        login_resp = client.post("/users/login", json={
            "username": "macro_alice",
            "password": "MacroPass123!",
        })
        token = login_resp.json()["access_token"]
        # Fetch user info
        user_resp = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
        user = next(u for u in user_resp.json() if u["username"] == "macro_alice")
        return user, {"Authorization": f"Bearer {token}"}

    assert resp.status_code == 201, resp.text
    user = resp.json()
    token = create_access_token({"sub": str(user["id"])})
    return user, {"Authorization": f"Bearer {token}"}


@pytest.fixture
def macro_user_b():
    """Register User B and return (user_dict, headers)."""
    resp = client.post("/users/register", json={
        "username": "macro_bob",
        "email": "macro_bob@example.com",
        "password": "MacroPass456!",
    })
    if resp.status_code == 409:
        login_resp = client.post("/users/login", json={
            "username": "macro_bob",
            "password": "MacroPass456!",
        })
        token = login_resp.json()["access_token"]
        user_resp = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
        user = next(u for u in user_resp.json() if u["username"] == "macro_bob")
        return user, {"Authorization": f"Bearer {token}"}

    assert resp.status_code == 201, resp.text
    user = resp.json()
    token = create_access_token({"sub": str(user["id"])})
    return user, {"Authorization": f"Bearer {token}"}


@pytest.fixture
def saved_macro(macro_user_a):
    """Create a sample macro for user A."""
    _user, headers = macro_user_a
    resp = client.post(
        "/macros/",
        json={
            "name": "hypotenuse",
            "expression": "root(add(power(a, 2), power(b, 2)), 2)"
        },
        headers=headers
    )
    assert resp.status_code == 201
    return resp.json()


def test_create_macro(macro_user_a):
    _user, headers = macro_user_a
    resp = client.post(
        "/macros/",
        json={
            "name": "compound_interest",
            "expression": "multiply(p, power(add(1, divide(r, n)), multiply(n, t)))"
        },
        headers=headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "compound_interest"
    assert "multiply" in data["expression"]


def test_create_macro_requires_auth():
    resp = client.post(
        "/macros/",
        json={"name": "test", "expression": "add(1, 2)"}
    )
    assert resp.status_code == 401


def test_list_macros(macro_user_a, saved_macro):
    _user, headers = macro_user_a
    resp = client.get("/macros/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert any(m["id"] == saved_macro["id"] for m in data)


def test_execute_inline_macro(macro_user_a):
    _user, headers = macro_user_a
    # Evaluates root(add(pow(3, 2), pow(4, 2)), 2) => root(add(9, 16), 2) => root(25, 2) => 5.0
    # Also tests alias 'pow' mapping to 'power'
    resp = client.post(
        "/macros/execute",
        json={
            "expression": "root(add(pow(a, 2), pow(b, 2)), 2)",
            "variables": {"a": 3.0, "b": 4.0}
        },
        headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == 5.0


def test_execute_stored_macro(macro_user_a, saved_macro):
    _user, headers = macro_user_a
    resp = client.post(
        "/macros/execute",
        json={
            "macro_id": saved_macro["id"],
            "variables": {"a": 3.0, "b": 4.0}
        },
        headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == 5.0


def test_execute_macro_unauthorized(macro_user_b, saved_macro):
    """User B cannot execute User A's stored macro by macro_id."""
    _user_b, headers_b = macro_user_b
    resp = client.post(
        "/macros/execute",
        json={
            "macro_id": saved_macro["id"],
            "variables": {"a": 3.0, "b": 4.0}
        },
        headers=headers_b
    )
    assert resp.status_code == 403


def test_execute_macro_not_found(macro_user_a):
    _user, headers = macro_user_a
    resp = client.post(
        "/macros/execute",
        json={"macro_id": 999999},
        headers=headers
    )
    assert resp.status_code == 404


def test_execute_macro_invalid_syntax(macro_user_a):
    _user, headers = macro_user_a
    resp = client.post(
        "/macros/execute",
        json={"expression": "add(1, "},
        headers=headers
    )
    assert resp.status_code == 422


def test_delete_macro(macro_user_a, saved_macro):
    _user, headers = macro_user_a
    resp = client.delete(f"/macros/{saved_macro['id']}", headers=headers)
    assert resp.status_code == 204

    # Verify it is removed
    list_resp = client.get("/macros/", headers=headers)
    assert not any(m["id"] == saved_macro["id"] for m in list_resp.json())


def test_create_macro_duplicate_name(macro_user_a, saved_macro):
    """Attempting to create a macro with the exact same name for the same user is rejected."""
    _user, headers = macro_user_a
    resp = client.post(
        "/macros/",
        json={"name": saved_macro["name"].upper(), "expression": "power(a, 2)"},
        headers=headers
    )
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"]


def test_execute_stored_macro_records_history(macro_user_a, saved_macro):
    """Executing a stored macro triggers automatic entry generation in calculation history."""
    _user, headers = macro_user_a
    # Execute the macro
    exec_resp = client.post(
        "/macros/execute",
        json={
            "macro_id": saved_macro["id"],
            "variables": {"a": 6.0, "b": 8.0}
        },
        headers=headers
    )
    assert exec_resp.status_code == 200

    # Fetch user calculations history to confirm entry injection
    calcs_resp = client.get("/calculations/", headers=headers)
    assert calcs_resp.status_code == 200
    history = calcs_resp.json()
    
    # Assert at least one history entry contains the macro symbol label
    assert any("⚡" in entry["type"] and entry["result"] == 10.0 for entry in history)
