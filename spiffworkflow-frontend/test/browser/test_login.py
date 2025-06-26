from playwright.sync_api import expect, BrowserContext

from helpers.login import login, logout
from helpers.playwright_setup import browser_context  # Import the fixture


def test_login(browser_context: BrowserContext):
    page = browser_context.new_page()
    login(page, "admin", "admin")


def test_logout(browser_context: BrowserContext):
    page = browser_context.new_page()
    login(page, "admin", "admin")
    logout(page)
    expect(
        page.get_by_text("This login form is for demonstration purposes only")
    ).to_be_visible()
