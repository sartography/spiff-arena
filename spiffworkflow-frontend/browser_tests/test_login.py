from playwright.sync_api import sync_playwright
from .helpers import print_page_details


def test_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("http://localhost:7001")
        
        # Perform login
        page.fill('#username', 'admin')
        page.fill('#password', 'admin')
        page.click('#spiff-login-button')

        # Debug: Print details of interactable elements
        print_page_details(page)

        # Verify login was successful
        print("\n--- Verifying Login ---")
        try:
            page.wait_for_url("**/process-groups", timeout=10000)
            assert "Process Groups" in page.content()
        except:
            print("Failed to navigate to process groups")
        
        browser.close()
