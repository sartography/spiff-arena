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
    
    # Enable console logging
    page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.type}: {msg.text}"))
    
    # Enable network logging
    def log_response(response):
        if "/process-models/" in response.url and "/import" in response.url:
            print(f"IMPORT API RESPONSE: {response.status} {response.url}")
        elif response.status >= 400:
            print(f"ERROR RESPONSE: {response.status} {response.url}")
    
    page.on("response", log_response)
    
    # Create a new process group first, so we have a valid group to import into
    page.goto("http://localhost:7001/process-groups/new")
    page.wait_for_timeout(1000)
    
    # Fill in the process group form
    page.get_by_label("Display Name").fill("Test Import Group")
    page.get_by_label("ID").fill("test-import-group")
    
    # Submit the form
    page.get_by_role("button", name="Submit").click()
    page.wait_for_timeout(2000)
    
    # Now go to create a new process model in this group
    page.goto("http://localhost:7001/process-models/test-import-group/new")
    page.wait_for_timeout(2000)
    page.screenshot(path="debug_screenshots/process_model_new_page.png")
    print("Process Model New page screenshot saved")
    
    # The import button should be visible on this page
    import_button = page.locator("button[data-testid='process-model-import-button']").first
    expect(import_button).to_be_visible()
    import_button.click()
    
    # Wait for the dialog
    page.wait_for_timeout(1000)  
    page.screenshot(path="debug_screenshots/import_dialog.png")
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
    
    # Wait for the import to complete and redirect to process model page
    # We expect to be redirected to a URL containing 'process-models' if successful
    try:
        # After clicking import, wait a bit for the API call to complete
        page.wait_for_timeout(3000)
        page.screenshot(path="debug_screenshots/after_import_click.png")
        print("Waited for import to process")
        
        # After successful import, we're redirected back to the process group page
        # Let's go there explicitly to check if our model was imported
        process_group_url = "http://localhost:7001/process-groups/test-import-group"
        page.goto(process_group_url)
        page.wait_for_timeout(2000)
        page.screenshot(path="debug_screenshots/process_group_page.png")
        
        # Need to expand the Process Models accordion to see the imported model
        process_models_accordion = page.get_by_text("Process Models").first
        if process_models_accordion.is_visible():
            process_models_accordion.click()
            page.wait_for_timeout(1000)
            page.screenshot(path="debug_screenshots/expanded_accordion.png")
            print("Expanded Process Models accordion")
        else:
            print("Process Models accordion not found or not visible")
            
        # Look for evidence of the imported model in the process group
        # The imported model should have "Minimal Example" as its display name
        print("Looking for the imported model card...")
        page.screenshot(path="debug_screenshots/looking_for_model.png")
        model_card = page.get_by_text("Minimal Example").first
        expect(model_card).to_be_visible(timeout=5000)
        print("Found 'Minimal Example' card, import successful!")
        
        print("Import process completed successfully!")
    except Exception as e:
        # If we hit an error, capture it and take a screenshot
        page.screenshot(path="debug_screenshots/import_error.png")
        print(f"Import appears to have failed: {str(e)}")
        
        # Check if there's an error message on the page
        try:
            error_message = page.locator(".MuiAlert-message").first
            if error_message.is_visible():
                error_text = error_message.text_content()
                print(f"Error message shown: {error_text}")
                
            # Get the current URL and HTML content for debugging
            current_url = page.url
            print(f"Current URL: {current_url}")
            
            # Try to get the full HTML to see what's on the page
            html_content = page.content()
            print(f"HTML snippet: {html_content[:500]}...")
            
            # Check network requests for API calls
            print("\nChecking for recent network requests:")
            page.wait_for_timeout(1000)  # Wait a bit
            
            # Look for any alert or error messages on the page
            error_alerts = page.locator(".MuiAlert-root")
            if error_alerts.count() > 0:
                print(f"Found {error_alerts.count()} alerts on the page:")
                for i in range(error_alerts.count()):
                    alert = error_alerts.nth(i)
                    alert_text = alert.text_content()
                    print(f"Alert {i+1}: {alert_text}")
            else:
                print("No alert messages found on the page.")
        except Exception as debug_ex:
            print(f"Debug error: {debug_ex}")
            
        raise e  # Re-raise the exception to make the test fail


if __name__ == "__main__":
    # For manual testing
    import sys
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context()
        test_process_model_import(context)
        browser.close()