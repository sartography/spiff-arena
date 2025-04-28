from playwright.sync_api import sync_playwright, expect
from .helpers.login import login

def test_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Use the login helper function
        login(page, "admin", "admin")

        # Wait for the element that indicates login succeeded
        expect(page.get_by_role('button', name='User Actions')).to_be_visible()

        browser.close()
