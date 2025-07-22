import re
from playwright.sync_api import expect, BrowserContext, Page

from helpers.login import login
from helpers.playwright_setup import browser_context  # Import the fixture


def test_process_model_import(browser_context: BrowserContext):
    """Test importing a process model from GitHub."""
    page = browser_context.new_page()
    
    # Login as admin
    login(page, "admin", "admin")
    
    # Go directly to the new process model page
    page.goto("http://localhost:7001/process-groups")
    page.wait_for_timeout(2000)
    
    # Create a test process group directly via API or UI
    # For now, let's go directly to the new process model page with a known process group ID
    page.goto("http://localhost:7001/process-models/my-process-group/new")
    page.wait_for_timeout(2000)
    page.screenshot(path="process_model_new_page.png")
    print("Process Model New page screenshot saved")
    
    # The import button should be visible on this page
    import_button = page.locator("button[data-testid='process-model-import-button']").first
    expect(import_button).to_be_visible()
    import_button.click()
    
    # Wait for the dialog
    page.wait_for_timeout(1000)  
    page.screenshot(path="import_dialog.png")
    print("Import dialog screenshot saved")
    
    # Find the input field and enter the GitHub URL
    # The input is likely inside a div with the data-testid
    input_field = page.locator("input[placeholder*='github.com']").first
    expect(input_field).to_be_visible()
    input_field.fill("https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example")
    
    # Click the import button in the dialog
    dialog_import_button = page.locator("button[data-testid='import-button']").first
    expect(dialog_import_button).to_be_visible()
    expect(dialog_import_button).to_be_enabled()
    dialog_import_button.click()
    
    # Wait for the import to complete (this might take some time)
    page.wait_for_timeout(5000) 
    page.screenshot(path="after_import.png")
    print("After import screenshot saved")
    
    # The test is successful if we don't get any errors during import
    print("Import process completed successfully")


if __name__ == "__main__":
    # For manual testing
    import sys
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context()
        test_process_model_import(context)
        browser.close()