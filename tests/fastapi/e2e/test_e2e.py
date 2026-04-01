import os
import time
from playwright.sync_api import sync_playwright

def test_addition_e2e():
    """Test basic addition and memory through the UI"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        url = os.getenv("TEST_URL", "http://localhost:8000")
        try:
            page.goto(url)

            page.fill("#a", "5")
            page.fill("#b", "5")
            page.click("button:has-text('Add (+)')")

            page.wait_for_selector('.success')
            result = page.inner_text("#result-text")
            assert "10" in result

            # Store in Memory
            page.fill("#a", "999")
            page.click("button:has-text('Store \\'A\\' to Memory')")
            time.sleep(1)

            # Recall Memory
            page.click("button:has-text('Recall Memory')")
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
        url = os.getenv("TEST_URL", "http://localhost:8000")
        try:
            page.goto(url)
            page.fill("#a", "10")
            page.fill("#b", "3")
            page.click("button:has-text('Subtract (-)')")

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
        url = os.getenv("TEST_URL", "http://localhost:8000")
        try:
            page.goto(url)
            page.fill("#a", "10")
            page.fill("#b", "0")
            page.click("button:has-text('Divide')")

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
        url = os.getenv("TEST_URL", "http://localhost:8000")
        try:
            # Perform a calculation first
            page.goto(url)
            page.fill("#a", "8")
            page.fill("#b", "2")
            page.click("button:has-text('Multiply')")
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
