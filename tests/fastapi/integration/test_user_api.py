"""
Integration Tests for User API
===============================

Tests the user register and login endpoints against an in-memory SQLite
database.  In CI these tests run against a real PostgreSQL service container.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.database import Base, get_db
from app.api.models import User
from main import app


# ---------- Test Database Setup ----------

SQLALCHEMY_TEST_DATABASE_URL = "sqlite://"  # In-memory SQLite

_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_get_db():
    """Provide a test database session."""
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    """Activate DB override, create tables before each test, drop after."""
    app.dependency_overrides[get_db] = _override_get_db
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)
    app.dependency_overrides.pop(get_db, None)


client = TestClient(app)


# ---------- Helpers ----------

def _register(username="alice", email="alice@example.com", password="securepassword123"):
    return client.post("/users/register", json={
        "username": username,
        "email": email,
        "password": password,
    })


# ---------- Registration Tests ----------


class TestRegisterUser:
    """Tests for POST /users/register"""

    def test_register_success(self):
        """Registering with valid data returns 201 and the user data."""
        response = _register()
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"
        assert "id" in data
        assert "created_at" in data
        # password must NOT appear in the response
        assert "password_hash" not in data
        assert "password" not in data

    def test_password_is_hashed(self):
        """The stored password should be a bcrypt hash, not plain text."""
        _register(username="bob", email="bob@example.com", password="plaintext_password")
        db = _SessionLocal()
        user = db.query(User).filter(User.username == "bob").first()
        db.close()
        assert user is not None
        assert user.password_hash != "plaintext_password"
        assert user.password_hash.startswith("$2b$")

    def test_duplicate_username_returns_409(self):
        """Registering with an existing username returns 409."""
        _register(username="alice", email="alice1@example.com")
        response = _register(username="alice", email="alice2@example.com")
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_duplicate_email_returns_409(self):
        """Registering with an existing email returns 409."""
        _register(username="user1", email="shared@example.com")
        response = _register(username="user2", email="shared@example.com")
        assert response.status_code == 409

    def test_invalid_email_returns_422(self):
        """Registering with an invalid email returns 422."""
        response = client.post("/users/register", json={
            "username": "baduser",
            "email": "not-an-email",
            "password": "password123",
        })
        assert response.status_code == 422

    def test_missing_fields_returns_422(self):
        """Registering without required fields returns 422."""
        response = client.post("/users/register", json={"username": "incomplete"})
        assert response.status_code == 422

    # Legacy POST /users/ route still works
    def test_legacy_create_user_endpoint(self):
        """POST /users/ (legacy alias) still returns 201."""
        response = client.post("/users/", json={
            "username": "legacy",
            "email": "legacy@example.com",
            "password": "password123",
        })
        assert response.status_code == 201


# ---------- Login Tests ----------


class TestLoginUser:
    """Tests for POST /users/login"""

    def test_login_success(self):
        """Login with correct credentials returns 200 and the user data."""
        _register(username="charlie", email="charlie@example.com", password="mypassword")
        response = client.post("/users/login", json={
            "username": "charlie",
            "password": "mypassword",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Since it's a JWT, let's verify we can decode it
        from app.api.security import decode_access_token
        payload = decode_access_token(data["access_token"])
        assert "sub" in payload

    def test_login_wrong_password_returns_401(self):
        """Login with incorrect password returns 401."""
        _register(username="dave", email="dave@example.com", password="rightpassword")
        response = client.post("/users/login", json={
            "username": "dave",
            "password": "wrongpassword",
        })
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user_returns_401(self):
        """Login for a user that doesn't exist returns 401."""
        response = client.post("/users/login", json={
            "username": "ghost",
            "password": "doesntmatter",
        })
        assert response.status_code == 401

    def test_login_missing_fields_returns_422(self):
        """Login without supplying required fields returns 422."""
        response = client.post("/users/login", json={"username": "only_name"})
        assert response.status_code == 422

    def test_login_returns_correct_user_id(self):
        """The user_id returned by login matches the one from registration."""
        reg = _register(username="eve", email="eve@example.com", password="pass123")
        registered_id = reg.json()["id"]

        login = client.post("/users/login", json={
            "username": "eve",
            "password": "pass123",
        })
        assert login.status_code == 200
        data = login.json()
        assert "access_token" in data
        
        from app.api.security import decode_access_token
        payload = decode_access_token(data["access_token"])
        assert payload["sub"] == str(registered_id)


# ---------- Get / List Tests (unchanged) ----------


class TestGetUser:
    """Tests for GET /users/{user_id}"""

    def test_get_user_by_id(self):
        """Retrieving an existing user by ID returns the correct data."""
        create_resp = _register(username="charlie", email="charlie@example.com")
        user_id = create_resp.json()["id"]

        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "charlie"
        assert data["email"] == "charlie@example.com"
        assert "password_hash" not in data

    def test_get_nonexistent_user_returns_404(self):
        """Requesting a non-existent user ID returns 404."""
        response = client.get("/users/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestListUsers:
    """Tests for GET /users/"""

    def test_list_users_empty(self):
        """Listing users when none exist returns an empty list."""
        response = client.get("/users/")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_users_multiple(self):
        """Listing users returns all created users."""
        _register(username="user_a", email="a@example.com")
        _register(username="user_b", email="b@example.com")

        response = client.get("/users/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert len(data) == 2
        usernames = {u["username"] for u in data}
        assert usernames == {"user_a", "user_b"}

class TestAdvancedProfile:
    """Validate Profile updates and Password changes."""
    
    def test_update_profile(self):
        # Register and Login
        _register(username="mike", email="mike@example.com", password="mikepassword")
        login_resp = client.post("/users/login", json={"username": "mike", "password": "mikepassword"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        resp = client.put(
            "/users/me/profile",
            json={"username": "mike_updated", "email": "mike_updated@example.com"},
            headers=headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "mike_updated"
        assert data["email"] == "mike_updated@example.com"

    def test_change_password(self):
        _register(username="sarah", email="sarah@example.com", password="oldpassword")
        login_resp = client.post("/users/login", json={"username": "sarah", "password": "oldpassword"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Change password
        resp = client.put(
            "/users/me/password",
            json={"current_password": "oldpassword", "new_password": "new_secure_password123"},
            headers=headers
        )
        assert resp.status_code == 200
        
        # Ensure login works with NEW password
        new_login = client.post(
            "/users/login",
            json={"username": "sarah", "password": "new_secure_password123"}
        )
        assert new_login.status_code == 200
        assert "access_token" in new_login.json()
        
        # Ensure login FAILS with OLD password
        old_login = client.post(
            "/users/login",
            json={"username": "sarah", "password": "oldpassword"}
        )
        assert old_login.status_code == 401
