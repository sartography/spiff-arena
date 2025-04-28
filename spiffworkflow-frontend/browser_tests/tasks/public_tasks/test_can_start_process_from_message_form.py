import sys
import os
import pytest
from playwright.sync_api import sync_playwright, expect

helpers_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../helpers"))
if helpers_path not in sys.path:
    sys.path.insert(0, helpers_path)
from login import login
from debug import print_page_details


def do_logout(page):
    # Attempt logout via the UI first, then fallback to clearing storage and tab.
    try:
        user_action_btn = page.get_by_text("User Actions", exact=True)
        if user_action_btn.count() > 0 and user_action_btn.first.is_visible():
            user_action_btn.first.click()
            logout_btn = page.get_by_text("Logout", exact=True)
            if logout_btn.count() > 0 and logout_btn.first.is_visible():
                logout_btn.first.click()
                # Wait and check if login is visible on the next page
                if page.locator("#spiff-login-button").is_visible(timeout=7000):
                    return
    except Exception:
        pass
    # Fallback: open a fresh new tab after removing the old context (simulate clearing history)
    page.context.clear_cookies()
    page.context.storage_state(path="/tmp/storage-state.json")
    page.close()
    # Open new tab and check for logout (should show login screen)
    new_page = page.context.new_page()
    new_page.goto("http://localhost:7001/sign-in")
    expect(new_page.locator("#username")).to_be_visible(timeout=10000)
    expect(new_page.locator("#password")).to_be_visible(timeout=10000)
    expect(new_page.locator("#spiff-login-button")).to_be_visible(timeout=10000)
    return new_page  # Return fresh page for next test section


def test_can_start_process_from_message_form():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1. Log in and log out to reset permissions
        page.goto("http://localhost:7001/sign-in")
        login(page, "admin", "admin")
        new_page = do_logout(page)
        if new_page is not None:
            page = new_page

        # 2. Go to the public form's URL
        page.goto("http://localhost:7001/public/misc:bounty_start_multiple_forms")

        # 3. Enter first name, submit
        page.fill("#root_firstName", "MyFirstName")
        page.get_by_text("Submit", exact=True).click()

        # 4. Enter last name, submit
        page.fill("#root_lastName", "MyLastName")
        page.get_by_text("Submit", exact=True).click()

        print("sure")
        # 5. Confirm the completion message is shown with combined name
        expect(
            page.get_by_text("We hear you. Your name is MyFirstName MyLastName.")
        ).to_be_visible()
        browser.close()
