from playwright.sync_api import sync_playwright
from .helpers.debug import print_page_details

def test_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Navigate to the sign-in page
        page.goto('http://localhost:7001')

        # Enter username and password and click login
        page.fill('#username', 'admin')
        page.fill('#password', 'admin')
        page.click('#spiff-login-button')

        # Debugging print
        print_page_details(page)

        # Wait for the element that indicates login succeeded
        assert page.get_by_role('button', name='User Actions').is_visible(), "Login failed: 'User Actions' button not found."

        browser.close()
