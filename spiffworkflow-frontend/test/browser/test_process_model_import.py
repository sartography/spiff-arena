import re
from playwright.sync_api import expect, BrowserContext, Page

from helpers.login import login
from helpers.playwright_setup import browser_context  # Import the fixture


def test_process_model_import(browser_context: BrowserContext):
    """Test importing a process model from GitHub."""
    page = browser_context.new_page()
    
    # Login as admin
    login(page, "admin", "admin")
    
    # Navigate to process groups page
    page.goto("http://localhost:7001/process-groups")
    # Wait for page to load
    page.wait_for_timeout(2000)
    
    # Click on the 'Create Process Model' button in the root process group
    # First find the Add button in the Process Models section
    add_model_button = page.get_by_test_id("create-process-model-button").first
    expect(add_model_button).to_be_visible()
    add_model_button.click()
    
    # Now we're on the New Process Model page
    # Look for the import button
    import_button = page.get_by_test_id("process-model-import-button")
    expect(import_button).to_be_visible()
    import_button.click()
    
    # Wait for the import dialog to appear
    dialog = page.get_by_text("Import Process Model from GitHub")
    expect(dialog).to_be_visible()
    
    # Enter the GitHub URL
    url_input = page.get_by_test_id("repository-url-input")
    expect(url_input).to_be_visible()
    url_input.fill("https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example")
    
    # Click the import button
    import_button = page.get_by_test_id("import-button")
    expect(import_button).to_be_enabled()
    import_button.click()
    
    # Wait for the import to complete and redirect to the process model page
    # We don't know what the exact URL will be, but it should contain "process-models"
    page.wait_for_url(re.compile(r"process-models/.+"))
    
    # Verify we're on a process model page
    expect(page).to_have_url(re.compile(r"process-models/.+"))
    
    # Verify the imported files
    # Look for BPMN diagram or process model details
    expect(page.get_by_text("Process Model Details")).to_be_visible()
    
    # Navigate to files tab to verify files were imported
    page.get_by_test_id("process-model-files-tab").click()
    
    # Check if process_model.json exists
    expect(page.get_by_text("process_model.json")).to_be_visible()
    
    # Check if a BPMN file exists
    expect(page.locator("text=.bpmn")).to_be_visible()


if __name__ == "__main__":
    # For manual testing
    import sys
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context()
        test_process_model_import(context)
        browser.close()