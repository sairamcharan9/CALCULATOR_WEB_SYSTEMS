"""
Playwright E2E Tests
====================

Browser end-to-end tests for the Advanced Web Calculator.
Requires the server to be running at TEST_URL (default: http://localhost:8000).

Run with:
    TEST_URL=http://localhost:8000 pytest tests/fastapi/e2e -v
"""

import os
import time
import uuid

import pytest
import httpx
from playwright.sync_api import sync_playwright, expect

BASE_URL = os.getenv("TEST_URL", "http://localhost:8000")


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def playwright_instance():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="module")
def browser(playwright_instance):
    browser_instance = playwright_instance.chromium.launch(headless=True)
    yield browser_instance
    browser_instance.close()


@pytest.fixture
def page(browser):
    """Provides a fresh isolated context and page per test."""
    context = browser.new_context()
    page_instance = context.new_page()
    yield page_instance
    context.close()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _register_user_via_api(username: str, email: str, password: str) -> httpx.Response:
    """Register a user directly via API (no browser) for test setup."""
    resp = httpx.post(
        f"{BASE_URL}/users/register",
        json={"username": username, "email": email, "password": password},
        timeout=10,
    )
    return resp


def _setup_user(unique_suffix: str):
    """Register a user via API and return (username, password)."""
    username = f"bread_{unique_suffix}"
    email    = f"{username}@example.com"
    password = "BreadTest123!"
    resp = _register_user_via_api(username, email, password)
    assert resp.status_code == 201, f"Setup failed: {resp.text}"
    return username, password


def _login_and_get_token(page, username: str, password: str) -> str:
    """Helper: log in via the /login page and return the stored JWT."""
    page.goto(f"{BASE_URL}/login")
    page.fill("#login-username", username)
    page.fill("#login-password", password)
    page.click("#login-btn")
    page.wait_for_url(BASE_URL + "/")
    token = page.evaluate("() => localStorage.getItem('auth_token')")
    assert token is not None and len(token) > 20, "JWT not stored after login"
    return token


def _inject_token_and_goto(page, token: str, url: str = BASE_URL):
    """
    Inject a JWT into localStorage WITHOUT a double-navigation:
    Use add_init_script so the token is available before the first paint.
    """
    page.add_init_script(f"""
        window.addEventListener('DOMContentLoaded', () => {{
            localStorage.setItem('auth_token', '{token}');
        }});
        // Also set synchronously in case the script runs early
        try {{ localStorage.setItem('auth_token', '{token}'); }} catch(e) {{}}
    """)
    page.goto(url)
    # Confirm the token is in place
    page.wait_for_function(
        f"() => localStorage.getItem('auth_token') === '{token}'"
    )


def _auth_setup(page):
    uid = uuid.uuid4().hex[:8]
    u, p = _setup_user(uid)
    _login_and_get_token(page, u, p)


# ─────────────────────────────────────────────────────────────────────────────
# Calculator UI tests
# ─────────────────────────────────────────────────────────────────────────────

def test_addition_e2e(page):
    """Test basic addition through the UI"""
    _auth_setup(page)
    page.goto(BASE_URL)
    page.wait_for_selector("#a")

    page.fill("#a", "5")
    page.fill("#b", "5")
    page.click("#op-add")

    expect(page.locator("#result-text")).to_contain_text("10", timeout=10000)


def test_subtraction_e2e(page):
    """Test subtraction through the UI"""
    _auth_setup(page)
    page.goto(BASE_URL)
    page.wait_for_selector("#a")
    page.fill("#a", "10")
    page.fill("#b", "3")
    page.click("#op-subtract")

    expect(page.locator("#result-text")).to_contain_text("7", timeout=10000)


def test_divide_by_zero_e2e(page):
    """Test that dividing by zero shows an error in the result display"""
    _auth_setup(page)
    page.goto(BASE_URL)
    page.wait_for_selector("#a")
    page.fill("#a", "10")
    page.fill("#b", "0")
    page.click("#op-divide")

    result_loc = page.locator("#result-text")
    expect(result_loc).to_have_class("error", timeout=10000)


def test_history_e2e(page):
    """Test that the dashboard stats panel loads after a calculation"""
    _auth_setup(page)
    page.goto(BASE_URL)
    page.wait_for_selector("#a")
    page.fill("#a", "8")
    page.fill("#b", "2")
    page.click("#op-multiply")
    expect(page.locator("#result-text")).to_contain_text("16", timeout=10000)

    # Switch to Dashboard Tab
    page.click("#tab-btn-dashboard")
    page.wait_for_selector("#analytics-panel", state="visible")

    # Click Refresh Stats
    page.click("button:has-text('Refresh Stats')")
    time.sleep(1)

    expect(page.locator("#stat-total")).to_be_visible()


# ─────────────────────────────────────────────────────────────────────────────
# Auth E2E tests — Module 13
# ─────────────────────────────────────────────────────────────────────────────

def test_register_valid_user_e2e(page):
    """POSITIVE — Register with valid data via the /register page."""
    unique_id = uuid.uuid4().hex[:8]
    email = f"testuser_{unique_id}@example.com"
    username = f"user_{unique_id}"
    password = "SecurePass123!"

    page.goto(f"{BASE_URL}/register")
    page.fill("#reg-email", email)
    page.fill("#reg-username", username)
    page.fill("#reg-password", password)
    page.fill("#reg-confirm", password)
    page.click("#register-btn")

    expect(page.locator("#alert-success")).to_be_visible(timeout=8000)
    expect(page.locator("#alert-success")).to_contain_text("Account created")


def test_login_valid_credentials_e2e(page):
    """POSITIVE — Login with correct credentials via the /login page."""
    unique_id = uuid.uuid4().hex[:8]
    username = f"logintest_{unique_id}"
    email = f"{username}@example.com"
    password = "ValidPass456!"

    resp = _register_user_via_api(username, email, password)
    assert resp.status_code == 201, f"Setup registration failed: {resp.text}"

    page.goto(f"{BASE_URL}/login")
    page.fill("#login-username", username)
    page.fill("#login-password", password)
    page.click("#login-btn")

    page.wait_for_url(BASE_URL + "/", timeout=8000)

    token = page.evaluate("() => localStorage.getItem('auth_token')")
    assert token is not None, "JWT was not stored in localStorage"
    assert len(token) > 20, f"JWT looks invalid (too short): '{token}'"


def test_register_short_password_e2e(page):
    """NEGATIVE — Register with a password shorter than 8 characters."""
    page.goto(f"{BASE_URL}/register")
    page.fill("#reg-email", "short@example.com")
    page.fill("#reg-username", "shortpwuser")
    page.fill("#reg-password", "abc")     # 3 chars — too short
    page.fill("#reg-confirm", "abc")
    page.click("#register-btn")

    expect(page.locator("#password-error")).to_be_visible(timeout=5000)
    expect(page.locator("#alert-success")).not_to_be_visible()


def test_login_wrong_password_e2e(page):
    """NEGATIVE — Login with a wrong password shows a 401 error in the UI."""
    unique_id = uuid.uuid4().hex[:8]
    username = f"wrongpw_{unique_id}"
    email = f"{username}@example.com"
    correct_password = "CorrectPass789!"

    resp = _register_user_via_api(username, email, correct_password)
    assert resp.status_code == 201, f"Setup registration failed: {resp.text}"

    page.goto(f"{BASE_URL}/login")
    page.fill("#login-username", username)
    page.fill("#login-password", "WrongPassword!")
    page.click("#login-btn")

    expect(page.locator("#alert-error")).to_be_visible(timeout=8000)
    expect(page.locator("#alert-success")).not_to_be_visible()

    token = page.evaluate("() => localStorage.getItem('auth_token')")
    assert token is None or token == "", "JWT should not be stored on failed login"


# ─────────────────────────────────────────────────────────────────────────────
# BREAD E2E tests — Calculations Module 14
# ─────────────────────────────────────────────────────────────────────────────

def test_browse_calculations_e2e(page):
    """POSITIVE — Browse: authenticated user sees the My Calculations table."""
    uid = uuid.uuid4().hex[:8]
    username, password = _setup_user(uid)

    _login_and_get_token(page, username, password)
    # Navigate to home (already redirected there after login)
    page.goto(BASE_URL)

    # The table lives on the Dashboard tab — switch to it
    page.click("#tab-btn-dashboard")
    page.wait_for_selector("#tab-dashboard.active", timeout=5000)

    expect(page.locator("#calc-table")).to_be_visible(timeout=8000)
    expect(page.locator("#browse-btn")).to_be_visible(timeout=5000)
    # Auth banner must NOT be visible (user is logged in)
    expect(page.locator("#auth-banner")).not_to_be_visible()


def test_add_calculation_e2e(page):
    """POSITIVE — Add: log in, compute, verify row appears in table."""
    uid = uuid.uuid4().hex[:8]
    username, password = _setup_user(uid)

    _login_and_get_token(page, username, password)
    page.goto(BASE_URL)
    page.wait_for_selector("#a", timeout=8000)

    page.fill("#a", "12")
    page.fill("#b", "4")
    page.click("#op-add")

    expect(page.locator("#result-text")).to_have_class("success", timeout=10000)
    expect(page.locator("#result-text")).to_contain_text("16")

    # Switch to Dashboard to verify the row was auto-saved
    page.click("#tab-btn-dashboard")
    page.wait_for_selector("#tab-dashboard.active", timeout=5000)

    expect(page.locator("#calc-tbody")).to_contain_text("16", timeout=10000)
    expect(page.locator("#calc-tbody")).to_contain_text("ADD")


def test_edit_calculation_e2e(page):
    """POSITIVE — Edit: save a calculation via API, click edit, update, verify."""
    uid = uuid.uuid4().hex[:8]
    username, password = _setup_user(uid)

    login_resp = httpx.post(
        f"{BASE_URL}/users/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]

    calc_resp = httpx.post(
        f"{BASE_URL}/calculations/",
        json={"a": 5.0, "b": 4.0, "type": "MULTIPLY"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert calc_resp.status_code == 201, f"Calc save failed: {calc_resp.text}"
    calc_id = calc_resp.json()["id"]

    # Inject token before first navigation — no double-load
    _inject_token_and_goto(page, token, BASE_URL)

    # Switch to Dashboard tab where the table lives
    page.click("#tab-btn-dashboard")
    page.wait_for_selector("#tab-dashboard.active", timeout=5000)

    page.wait_for_selector(f"#edit-btn-{calc_id}", timeout=10000)
    page.click(f"#edit-btn-{calc_id}")

    expect(page.locator("#edit-modal")).to_be_visible(timeout=5000)

    page.fill("#edit-a", "6")
    page.fill("#edit-b", "7")
    page.select_option("#edit-type", "MULTIPLY")
    page.click("#edit-save-btn")

    expect(page.locator("#edit-modal")).not_to_be_visible(timeout=8000)
    expect(page.locator("#calc-tbody")).to_contain_text("42", timeout=10000)


def test_delete_calculation_e2e(page):
    """POSITIVE — Delete: save a calculation via API, click delete, verify gone."""
    uid = uuid.uuid4().hex[:8]
    username, password = _setup_user(uid)

    login_resp = httpx.post(
        f"{BASE_URL}/users/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]

    calc_resp = httpx.post(
        f"{BASE_URL}/calculations/",
        json={"a": 99.0, "b": 1.0, "type": "ADD"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert calc_resp.status_code == 201, f"Calc save failed: {calc_resp.text}"
    calc_id = calc_resp.json()["id"]

    _inject_token_and_goto(page, token, BASE_URL)

    # Switch to Dashboard tab
    page.click("#tab-btn-dashboard")
    page.wait_for_selector("#tab-dashboard.active", timeout=5000)

    page.wait_for_selector(f"#delete-btn-{calc_id}", timeout=10000)

    page.on("dialog", lambda dialog: dialog.accept())
    page.click(f"#delete-btn-{calc_id}")

    expect(page.locator(f"#row-{calc_id}")).not_to_be_visible(timeout=8000)


def test_unauthenticated_browse_e2e(page):
    """NEGATIVE — Browse without login: User is instantly redirected to /login."""
    # Start on login page to ensure no stale token
    page.goto(BASE_URL + "/login")
    page.evaluate("() => localStorage.removeItem('auth_token')")

    # Now attempt to visit home
    page.goto(BASE_URL)

    # The JS redirect guard should push us back to /login
    page.wait_for_selector("#login-btn", state="visible", timeout=8000)
    expect(page.locator("#login-btn")).to_be_visible()
    assert "/login" in page.url, f"Expected redirect to /login, but URL is {page.url}"


def test_add_missing_operand_validation_e2e(page):
    """NEGATIVE — Divide-by-zero shows error and hides Save button."""
    uid = uuid.uuid4().hex[:8]
    username, password = _setup_user(uid)

    _login_and_get_token(page, username, password)
    page.goto(BASE_URL)
    page.wait_for_selector("#a", timeout=8000)

    page.fill("#a", "10")
    page.fill("#b", "0")
    page.click("#op-divide")

    # The result-text element must have class "error"
    expect(page.locator("#result-text")).to_have_class("error", timeout=10000)

    # Save button must NOT appear after a divide-by-zero error
    time.sleep(0.5)
    expect(page.locator("#save-btn")).not_to_be_visible()



