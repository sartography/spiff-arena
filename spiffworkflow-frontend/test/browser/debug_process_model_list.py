import os
from playwright.sync_api import sync_playwright

from helpers.login import login

def debug_page():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # Login
        login(page, "admin", "admin")
        
        # Navigate to process groups
        page.goto("http://localhost:7001/process-groups")
        
        # Wait for page to load
        page.wait_for_timeout(2000)
        
        # Save a screenshot
        os.makedirs("debug_screenshots", exist_ok=True)
        page.screenshot(path="debug_screenshots/process_groups_page.png")
        
        # List all elements with data-testid attribute
        print("\nElements with data-testid:")
        for element in page.query_selector_all("[data-testid]"):
            test_id = element.get_attribute("data-testid")
            tag_name = element.evaluate("el => el.tagName")
            print(f"- {tag_name}: {test_id}")
            
        # Keep the browser open for manual inspection
        print("\nBrowser will remain open for 60 seconds for manual inspection...")
        page.wait_for_timeout(60000)
        
        # Close the browser
        browser.close()

if __name__ == "__main__":
    debug_page()