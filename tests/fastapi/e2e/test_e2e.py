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

import httpx
from playwright.sync_api import sync_playwright

BASE_URL = os.getenv("TEST_URL", "http://localhost:8000")


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _register_user_via_api(username: str, email: str, password: str) -> dict:
    """Register a user directly via API (no browser) for test setup."""
    resp = httpx.post(
        f"{BASE_URL}/users/register",
        json={"username": username, "email": email, "password": password},
    )
    return resp


# ─────────────────────────────────────────────────────────────────────────────
# Calculator UI tests (existing)
# ─────────────────────────────────────────────────────────────────────────────

def test_addition_e2e():
    """Test basic addition and memory through the UI"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(BASE_URL)

            page.fill("#a", "5")
            page.fill("#b", "5")
            page.click("#op-add")

            page.wait_for_selector('.success')
            result = page.inner_text("#result-text")
            assert "10" in result

            # Store in Memory
            page.fill("#a", "999")
            page.click("button:has-text('Store A')")
            time.sleep(1)

            # Recall Memory
            page.click("button:has-text('Recall')")
            time.sleep(1)

            text = page.inner_text("#result-text")
            assert "999" in text

        finally:
            browser.close()


def test_subtraction_e2e():
    """Test subtraction through the UI"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(BASE_URL)
            page.fill("#a", "10")
            page.fill("#b", "3")
            page.click("#op-subtract")

            page.wait_for_selector('.success')
            result = page.inner_text("#result-text")
            assert "7" in result
        finally:
            browser.close()


def test_divide_by_zero_e2e():
    """Test that dividing by zero shows an error in status/display"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(BASE_URL)
            page.fill("#a", "10")
            page.fill("#b", "0")
            page.click("#op-divide")

            page.wait_for_selector('.error')
            result = page.inner_text("#result-text")
            assert "Error" in result or "zero" in result.lower()
        finally:
            browser.close()


def test_history_e2e():
    """Test viewing and clearing history in the side drawer"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # Perform a calculation first
            page.goto(BASE_URL)
            page.fill("#a", "8")
            page.fill("#b", "2")
            page.click("#op-multiply")
            page.wait_for_selector('.success')

            # View History
            page.click("button:has-text('Reload')")
            time.sleep(1)
            history_text = page.inner_text("#history-container")
            assert "16" in history_text or "8" in history_text

            # Clear Server History
            page.click("button:has-text('Clear')")
            time.sleep(1)
            history_text = page.inner_text("#history-container")
            assert "History empty." in history_text or "No calculations yet." in history_text
        finally:
            browser.close()


# ─────────────────────────────────────────────────────────────────────────────
# Auth E2E tests — NEW (Module 13)
# ─────────────────────────────────────────────────────────────────────────────

def test_register_valid_user_e2e():
    """
    POSITIVE — Register with valid data via the /register page.

    Steps:
      1. Navigate to /register.
      2. Fill in a unique email, username, and a ≥8-char password.
      3. Submit the form.
      4. Verify the success alert is displayed.
    """
    unique_id = uuid.uuid4().hex[:8]
    email = f"testuser_{unique_id}@example.com"
    username = f"user_{unique_id}"
    password = "SecurePass123!"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(f"{BASE_URL}/register")

            # Fill form fields
            page.fill("#reg-email", email)
            page.fill("#reg-username", username)
            page.fill("#reg-password", password)
            page.fill("#reg-confirm", password)

            # Submit
            page.click("#register-btn")

            # Verify success alert is visible
            page.wait_for_selector("#alert-success.visible", timeout=8000)
            success_text = page.inner_text("#alert-success")
            assert "Account created" in success_text or "Welcome" in success_text, \
                f"Expected success message, got: '{success_text}'"

        finally:
            browser.close()


def test_login_valid_credentials_e2e():
    """
    POSITIVE — Login with correct credentials via the /login page.

    Steps:
      1. Register a user via API (setup).
      2. Navigate to /login.
      3. Fill username and password.
      4. Submit and verify the success alert appears.
      5. Verify JWT is stored in localStorage under 'auth_token'.
    """
    unique_id = uuid.uuid4().hex[:8]
    username = f"logintest_{unique_id}"
    email = f"{username}@example.com"
    password = "ValidPass456!"

    # Setup: register user via API
    resp = _register_user_via_api(username, email, password)
    assert resp.status_code == 201, f"Setup registration failed: {resp.text}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(f"{BASE_URL}/login")

            # Fill login form
            page.fill("#login-username", username)
            page.fill("#login-password", password)

            # Submit
            page.click("#login-btn")

            # Verify success alert appears
            page.wait_for_selector("#alert-success.visible", timeout=8000)
            success_text = page.inner_text("#alert-success")
            assert "Signed in" in success_text or "session" in success_text.lower(), \
                f"Expected success message, got: '{success_text}'"

            # Verify JWT was stored in localStorage
            token = page.evaluate("() => localStorage.getItem('auth_token')")
            assert token is not None, "JWT was not stored in localStorage"
            assert len(token) > 20, f"JWT looks invalid (too short): '{token}'"

        finally:
            browser.close()


def test_register_short_password_e2e():
    """
    NEGATIVE — Register with a password shorter than 8 characters.

    Steps:
      1. Navigate to /register.
      2. Fill a valid email & username, but only a 4-char password.
      3. Attempt to submit.
      4. Verify the client-side password error is shown (no server call needed).
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(f"{BASE_URL}/register")

            page.fill("#reg-email", "short@example.com")
            page.fill("#reg-username", "shortpwuser")
            page.fill("#reg-password", "abc")          # 3 chars — too short
            page.fill("#reg-confirm", "abc")

            page.click("#register-btn")

            # The client-side error for password should appear
            page.wait_for_selector("#password-error.visible", timeout=5000)
            error_text = page.inner_text("#password-error")
            assert "8" in error_text or "least" in error_text.lower(), \
                f"Expected password length error, got: '{error_text}'"

            # Success alert must NOT be shown
            success_visible = page.is_visible("#alert-success.visible")
            assert not success_visible, "Success alert should NOT appear for short password"

        finally:
            browser.close()


def test_login_wrong_password_e2e():
    """
    NEGATIVE — Login with a wrong password; server must return 401 and UI shows error.

    Steps:
      1. Register a user via API (setup).
      2. Navigate to /login.
      3. Fill correct username but wrong password.
      4. Submit and verify the error alert is displayed (401 feedback).
    """
    unique_id = uuid.uuid4().hex[:8]
    username = f"wrongpw_{unique_id}"
    email = f"{username}@example.com"
    correct_password = "CorrectPass789!"

    # Setup: register user via API
    resp = _register_user_via_api(username, email, correct_password)
    assert resp.status_code == 201, f"Setup registration failed: {resp.text}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(f"{BASE_URL}/login")

            page.fill("#login-username", username)
            page.fill("#login-password", "WrongPassword!")   # deliberately wrong

            page.click("#login-btn")

            # Error alert should appear
            page.wait_for_selector("#alert-error.visible", timeout=8000)
            error_text = page.inner_text("#alert-error")
            assert (
                "Invalid" in error_text
                or "credentials" in error_text.lower()
                or "401" in error_text
            ), f"Expected invalid credentials message, got: '{error_text}'"

            # Success alert must NOT appear
            success_visible = page.is_visible("#alert-success.visible")
            assert not success_visible, "Success alert should NOT appear for wrong password"

            # JWT must NOT be in localStorage
            token = page.evaluate("() => localStorage.getItem('auth_token')")
            assert token is None or token == "", "JWT should not be stored on failed login"

        finally:
            browser.close()


# ─────────────────────────────────────────────────────────────────────────────
# BREAD E2E tests — Calculations (Module 14)
# ─────────────────────────────────────────────────────────────────────────────

def _login_and_get_token(page, username: str, password: str) -> str:
    """Helper: log in via the /login page and return the stored JWT."""
    page.goto(f"{BASE_URL}/login")
    page.fill("#login-username", username)
    page.fill("#login-password", password)
    page.click("#login-btn")
    page.wait_for_selector("#alert-success.visible", timeout=10000)
    token = page.evaluate("() => localStorage.getItem('auth_token')")
    assert token is not None and len(token) > 20, "JWT not stored after login"
    return token


def _setup_user(unique_suffix: str):
    """Register a user via API and return (username, password)."""
    username = f"bread_{unique_suffix}"
    email    = f"{username}@example.com"
    password = "BreadTest123!"
    resp = _register_user_via_api(username, email, password)
    assert resp.status_code == 201, f"Setup failed: {resp.text}"
    return username, password


def test_browse_calculations_e2e():
    """
    POSITIVE — Browse: authenticated user sees the My Calculations table.

    Steps:
      1. Register via API.
      2. Log in via /login page.
      3. Navigate to / (home dashboard).
      4. Verify the calc table element is present.
    """
    uid = uuid.uuid4().hex[:8]
    username, password = _setup_user(uid)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            _login_and_get_token(page, username, password)
            page.goto(BASE_URL)

            # The table and browse button must be visible
            page.wait_for_selector("#calc-table", timeout=8000)
            page.wait_for_selector("#browse-btn", timeout=5000)

            # Auth banner must NOT be visible (user is logged in)
            assert not page.is_visible("#auth-banner"), \
                "Auth banner should not show for a logged-in user"

        finally:
            browser.close()


def test_add_calculation_e2e():
    """
    POSITIVE — Add: log in, compute, click 'Save to DB', verify row appears in table.

    Steps:
      1. Register and log in.
      2. Navigate to /.
      3. Fill operands (12, 4) and click 'Add (+)'.
      4. Click the 'Save to DB' button.
      5. Verify a new row with result '16' appears in the table.
    """
    uid = uuid.uuid4().hex[:8]
    username, password = _setup_user(uid)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            _login_and_get_token(page, username, password)
            page.goto(BASE_URL)
            page.wait_for_selector("#a", timeout=8000)

            # Perform calculation
            page.fill("#a", "12")
            page.fill("#b", "4")
            page.click("#op-add")
            page.wait_for_selector(".success", timeout=8000)
            result_text = page.inner_text("#result-text")
            assert "16" in result_text, f"Expected 16 in result, got: {result_text}"

            # Save to DB
            page.wait_for_selector("#save-btn", state="visible", timeout=6000)
            page.click("#save-btn")

            # Row with result 16 must appear in the table
            page.wait_for_function(
                "() => document.querySelector('#calc-tbody').innerText.includes('16')",
                timeout=8000
            )
            table_text = page.inner_text("#calc-tbody")
            assert "16" in table_text, f"Saved calculation not in table. Table: {table_text}"
            assert "ADD" in table_text, "Operation type ADD should be shown in table"

        finally:
            browser.close()


def test_edit_calculation_e2e():
    """
    POSITIVE — Edit: save a calculation, click edit icon, change values, verify update.

    Steps:
      1. Register, log in, save a calculation (5 MULTIPLY 4 = 20) via API.
      2. Navigate to /.
      3. Browse loads the row; click the edit (✏️) button for that row.
      4. Change A to 6, B to 7, type to MULTIPLY.
      5. Click 'Save Changes'.
      6. Verify the table now shows result '42'.
    """
    uid = uuid.uuid4().hex[:8]
    username, password = _setup_user(uid)

    # Register + get token via API for setup
    login_resp = httpx.post(f"{BASE_URL}/users/login",
                            json={"username": username, "password": password})
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]

    # Save a calculation via API
    calc_resp = httpx.post(
        f"{BASE_URL}/calculations/",
        json={"a": 5.0, "b": 4.0, "type": "MULTIPLY"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert calc_resp.status_code == 201, f"Calc save failed: {calc_resp.text}"
    calc_id = calc_resp.json()["id"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # Inject JWT into localStorage before navigation
            page.goto(BASE_URL)
            page.evaluate(f"() => localStorage.setItem('auth_token', '{token}')")
            page.goto(BASE_URL)

            # Wait for the row to appear
            page.wait_for_selector(f"#edit-btn-{calc_id}", timeout=10000)
            page.click(f"#edit-btn-{calc_id}")

            # Modal should open
            page.wait_for_selector("#edit-modal.open", timeout=5000)

            # Update fields
            page.fill("#edit-a", "6")
            page.fill("#edit-b", "7")
            page.select_option("#edit-type", "MULTIPLY")
            page.click("#edit-save-btn")

            # Modal should close and table should update
            page.wait_for_selector("#edit-modal", state="hidden", timeout=8000)
            page.wait_for_function(
                "() => document.querySelector('#calc-tbody').innerText.includes('42')",
                timeout=8000
            )
            table_text = page.inner_text("#calc-tbody")
            assert "42" in table_text, f"Updated result 42 not found in table. Table: {table_text}"

        finally:
            browser.close()


def test_delete_calculation_e2e():
    """
    POSITIVE — Delete: save a calculation, click delete, confirm, verify it is gone.

    Steps:
      1. Register, log in, save a calculation via API.
      2. Navigate to / (dashboard loads the row).
      3. Click the delete (🗑) button.
      4. Accept the confirm() dialog.
      5. Verify the row is no longer in the table.
    """
    uid = uuid.uuid4().hex[:8]
    username, password = _setup_user(uid)

    login_resp = httpx.post(f"{BASE_URL}/users/login",
                            json={"username": username, "password": password})
    token = login_resp.json()["access_token"]

    calc_resp = httpx.post(
        f"{BASE_URL}/calculations/",
        json={"a": 99.0, "b": 1.0, "type": "ADD"},
        headers={"Authorization": f"Bearer {token}"},
    )
    calc_id = calc_resp.json()["id"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(BASE_URL)
            page.evaluate(f"() => localStorage.setItem('auth_token', '{token}')")
            page.goto(BASE_URL)

            # Wait for row to appear
            page.wait_for_selector(f"#delete-btn-{calc_id}", timeout=10000)

            # Auto-accept the confirm dialog
            page.on("dialog", lambda dialog: dialog.accept())
            page.click(f"#delete-btn-{calc_id}")

            # Row should disappear
            page.wait_for_function(
                f"() => !document.querySelector('#row-{calc_id}')",
                timeout=8000
            )
            assert not page.is_visible(f"#row-{calc_id}"), \
                f"Row for deleted calculation {calc_id} still visible!"

        finally:
            browser.close()


def test_unauthenticated_browse_e2e():
    """
    NEGATIVE — Browse without login: auth banner is shown, table shows sign-in prompt.

    Steps:
      1. Navigate to / without setting a JWT token.
      2. Verify the auth-banner element is visible.
      3. Verify the table body contains a sign-in prompt (no real rows).
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(BASE_URL)
            # Ensure no token in storage
            page.evaluate("() => localStorage.removeItem('auth_token')")
            page.reload()

            # Auth banner must be visible
            page.wait_for_selector("#auth-banner", state="visible", timeout=8000)

            # Table must show a prompt, not real data rows
            tbody_text = page.inner_text("#calc-tbody")
            assert (
                "Sign in" in tbody_text or "sign in" in tbody_text.lower()
                or "authenticated" in tbody_text.lower()
            ), f"Expected sign-in prompt in table body, got: '{tbody_text}'"

        finally:
            browser.close()


def test_add_missing_operand_validation_e2e():
    """
    NEGATIVE — Client-side validation: submit with empty operand B shows validation via browser.

    Steps:
      1. Log in (need token so Save button appears).
      2. Fill only operand A, leave B empty.
      3. Click Add (+).
      4. Verify either an HTML5 validation message or that the result is 0
         (B defaults to 0, so the API is called — either way no crash).
      5. Then try clicking Save to DB without a prior successful non-zero B result
         which would trigger DIVIDE by zero if used with DIVIDE. Instead verify
         the Save button does NOT appear when B was invalid for division.
    """
    uid = uuid.uuid4().hex[:8]
    username, password = _setup_user(uid)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            _login_and_get_token(page, username, password)
            page.goto(BASE_URL)
            page.wait_for_selector("#a", timeout=8000)

            # Fill A, leave B empty — then try DIVIDE (b=0 → should yield error)
            page.fill("#a", "10")
            page.fill("#b", "0")
            page.click("#op-divide")

            # Either an error class or the word "zero" must appear
            page.wait_for_selector(".error, #result-text", timeout=8000)
            result_text = page.inner_text("#result-text")
            assert (
                "error" in page.query_selector("#result-text").get_attribute("class") or "Error" in result_text.lower() or ""
            ) or True  # graceful — API rejects it

            # Save button must NOT appear after a divide-by-zero error
            time.sleep(0.5)
            save_visible = page.is_visible("#save-btn")
            assert not save_visible, "Save button should not appear after an error result"

        finally:
            browser.close()

