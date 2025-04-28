import sys
import os
import pytest
from playwright.sync_api import expect, Page, BrowserContext

# Add helpers dir to path if not already present
# Consider using pytest's pythonpath configuration or project structure instead
helpers_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../helpers"))
if helpers_path not in sys.path:
    sys.path.insert(0, helpers_path)

from login import login
from debug import print_page_details
from playwright_setup import browser_context  # Import the fixture


def do_logout(page: Page, context: BrowserContext):
    """Logs out the user, handling potential UI issues and returning a fresh page."""
    try:
        user_action_btn = page.get_by_text("User Actions", exact=True)
        if user_action_btn.count() > 0 and user_action_btn.first.is_visible():
            user_action_btn.first.click()
            logout_btn = page.get_by_text("Logout", exact=True)
            if logout_btn.count() > 0 and logout_btn.first.is_visible():
                logout_btn.first.click()
                # Wait and check if login is visible on the next page
                if page.locator("#spiff-login-button").is_visible(timeout=7000):
                    return page  # Return the same page if logout UI worked
    except Exception as e:
        print(f"Standard logout failed, attempting fallback: {e}")
        pass  # Proceed to fallback

    # Fallback: Clear context state and open a fresh new tab
    print("Executing logout fallback: clearing context and opening new page.")
    try:
        context.clear_cookies()
        # Saving state might not be necessary unless debugging specific session issues
        # context.storage_state(path="/tmp/storage-state.json")
        page.close()
    except Exception as e:
        print(f"Error during page close/context clear: {e}")
        # If page close fails, context might still be usable for new_page

    # Open new tab and check for logout (should show login screen)
    new_page = context.new_page()
    new_page.goto("http://localhost:7001/sign-in")
    expect(new_page.locator("#username")).to_be_visible(timeout=10000)
    expect(new_page.locator("#password")).to_be_visible(timeout=10000)
    expect(new_page.locator("#spiff-login-button")).to_be_visible(timeout=10000)
    return new_page  # Return fresh page


def test_can_start_process_from_message_form(browser_context: BrowserContext):
    """Tests starting a process via a public message form."""
    page = browser_context.new_page()

    # 1. Log in and log out to reset permissions
    page.goto("http://localhost:7001/sign-in")
    login(page, "admin", "admin")
    page = do_logout(page, browser_context) # Pass context, update page reference

    # 2. Go to the public form's URL
    page.goto("http://localhost:7001/public/misc:bounty_start_multiple_forms")

    # 3. Enter first name, submit
    page.fill("#root_firstName", "MyFirstName")
    page.get_by_text("Submit", exact=True).click()

    # 4. Enter last name, submit
    page.fill("#root_lastName", "MyLastName")
    page.get_by_text("Submit", exact=True).click()

    # 5. Confirm the completion message is shown with combined name
    expect(
        page.get_by_text("We hear you. Your name is MyFirstName MyLastName.")
    ).to_be_visible()

    # No need to close browser here, fixture handles it
