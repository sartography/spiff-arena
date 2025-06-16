import re
from playwright.sync_api import Page, expect, BrowserContext

from helpers.playwright_setup import browser_context # Fixture import
from helpers.login import BASE_URL # Only import BASE_URL
from helpers.debug import print_page_details 

def test_can_complete_guest_task(browser_context: BrowserContext): 
    page = browser_context.new_page()
    page.goto(BASE_URL) 

    # --- Start of inlined login logic ---
    expect(page.get_by_text("This login form is for demonstration purposes only")).to_be_visible(timeout=10000)
    page.locator("#username").fill("admin")
    page.locator("#password").fill("admin")
    page.locator('button:has-text("Login")').click()
    # Wait for successful login - check for an element on the landing page
    expect(page.get_by_role("link", name="Dashboard")).to_be_visible(timeout=10000)
    # --- End of inlined login logic ---

    # Navigate to process model
    page.get_by_role("link", name="Processes", exact=True).click()
    expect(page.get_by_role("heading", name="Process Models")).to_be_visible()

    page.get_by_role("link", name="Shared Resources", exact=True).click()
    expect(page.get_by_role("link", name="task-with-guest-form", exact=True)).to_be_visible()

    page.get_by_role("link", name="task-with-guest-form", exact=True).click()
    expect(page.get_by_role("heading", name="task-with-guest-form")).to_be_visible()

    # Run the primary BPMN file
    page.get_by_test_id("run-model-button").click()
    run_dialog = page.get_by_role("dialog", name="Run process model")
    expect(run_dialog).to_be_visible()
    run_dialog.get_by_role("button", name="Run").click()

    # Extract the guest task public link
    expect(page.get_by_text("Process Instance Details")).to_be_visible(timeout=15000) 
    
    first_task_url_element = page.locator('[data-testid="metadata-value-first_task_url"] a')
    expect(first_task_url_element).to_be_visible(timeout=10000)
    guest_task_url = first_task_url_element.get_attribute("href")
    assert guest_task_url is not None, "Guest task URL should not be None"
    assert guest_task_url.startswith("/"), f"Guest task URL should be a relative path starting with /, but was {guest_task_url}"

    # Log out
    page.get_by_role("button", name="admin@example.com").click()
    page.get_by_role("menuitem", name="Sign out").click()
    expect(page.locator('button:has-text("Login")')).to_be_visible()

    # Visit public guest/task URL as a guest
    full_guest_task_url = BASE_URL + guest_task_url 
    page.goto(full_guest_task_url)
    
    expect(page.get_by_text("Complete Your Task", exact=False)).to_be_visible(timeout=20000) 

    # Form 1
    submit_button_form1 = page.get_by_role("button", name="Submit")
    expect(submit_button_form1).to_be_visible()
    submit_button_form1.click()

    # Form 2
    submit_button_form2 = page.get_by_role("button", name="Submit") 
    expect(submit_button_form2).to_be_visible(timeout=15000) 
    submit_button_form2.click()

    # Confirm completion message
    expect(page.get_by_text("You are done. Yay!")).to_be_visible(timeout=15000)

    # Check the link cannot be reused
    page.goto(full_guest_task_url)
    expect(page.get_by_text("Error retrieving content.")).to_be_visible(timeout=10000)

    # Click the public home link
    page.get_by_test_id("public-home-link").click()
    expect(page.get_by_test_id("public-sign-out")).to_be_visible()

    # Click sign out
    page.get_by_test_id("public-sign-out").click()

    # Ensure redirection to sign-in page or login button
    expect(page.locator('button:has-text("Login")')).to_be_visible()
