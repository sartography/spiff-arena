import sys
import os
from playwright.sync_api import expect, BrowserContext

# Add helpers dir to path if not already present
# Consider using pytest's pythonpath configuration or project structure instead
# helpers_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "helpers"))
# if helpers_path not in sys.path:
#     sys.path.insert(0, helpers_path)

from .helpers.login import login, logout
from .helpers.playwright_setup import browser_context  # Import the fixture


def test_login(browser_context: BrowserContext):
    """Tests the standard login flow."""
    page = browser_context.new_page()

    # Use the login helper function
    login(page, "admin", "admin")


def test_logout(browser_context: BrowserContext):
    """Tests the logout functionality and verifies the login page content."""
    page = browser_context.new_page()
    login(page, "admin", "admin")
    logout(page)
    expect(
        page.get_by_text("This login form is for demonstration purposes only")
    ).to_be_visible()
