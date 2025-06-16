import re
from playwright.sync_api import Page, expect, BrowserContext

from helpers.playwright_setup import browser_context 
from helpers.login import BASE_URL 
from helpers.debug import print_page_details

def test_can_complete_guest_task(browser_context: BrowserContext): 
    page = browser_context.new_page()
    
    # --- Start of corrected login logic ---
    sign_in_url = BASE_URL + "/auth/sign-in" 
    page.goto(sign_in_url)
    # print_page_details(page) # Keep for debugging if login still fails

    # Use placeholder locators as IDs seem to be missing on the login page
    expect(page.get_by_placeholder("Username", exact=False)).to_be_visible(timeout=10000)
    page.get_by_placeholder("Username", exact=False).fill("admin")
    page.get_by_placeholder("Password", exact=False).fill("admin")
    page.get_by_role("button", name="Login").click() # Use role and name for login button
    
    # Wait for successful login - check for User Actions button
    expect(page.get_by_role("button", name="User Actions")).to_be_visible(timeout=10000) 
    # --- End of corrected login logic ---

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
    expect(page.get_by_text("Process Instance Details")).to_be_visible(timeout=20000) 
    
    first_task_url_element = page.locator('[data-testid="metadata-value-first_task_url"] a')
    expect(first_task_url_element).to_be_visible(timeout=15000)
    guest_task_url = first_task_url_element.get_attribute("href")
    assert guest_task_url is not None, "Guest task URL should not be None"
    assert guest_task_url.startswith("/"), f"Guest task URL ({guest_task_url}) should be a relative path starting with /"

    # --- Start of corrected logout logic ---
    user_menu_button = page.get_by_role("button", name="User Actions")
    expect(user_menu_button).to_be_visible()
    user_menu_button.click()
    page.locator('[data-testid="sign-out-button"]').click()
    # Ensure logout is complete by checking for the login button on the login page
    expect(page.get_by_role("button", name="Login")).to_be_visible(timeout=10000) # Corrected selector
    expect(page.get_by_text("This login form is for demonstration purposes only")).to_be_visible(timeout=5000)
    # --- End of corrected logout logic ---

    # Visit public guest/task URL as a guest
    full_guest_task_url = BASE_URL + guest_task_url 
    page.goto(full_guest_task_url)
    
    expect(page.get_by_text("Complete Your Task", exact=False)).to_be_visible(timeout=25000) 

    # Form 1
    submit_button_form1 = page.get_by_role("button", name="Submit")
    expect(submit_button_form1).to_be_visible()
    expect(submit_button_form1).to_be_enabled() 
    submit_button_form1.click()

    # Form 2
    submit_button_form2 = page.get_by_role("button", name="Submit") 
    expect(submit_button_form2).to_be_visible(timeout=15000) 
    expect(submit_button_form2).to_be_enabled() 
    submit_button_form2.click()

    # Confirm completion message
    expect(page.get_by_text("You are done. Yay!")).to_be_visible(timeout=15000)

    # Check the link cannot be reused
    page.goto(full_guest_task_url) 
    expect(page.get_by_text("Error retrieving content.")).to_be_visible(timeout=10000)

    # Click the public home link
    public_home_link = page.get_by_test_id("public-home-link")
    expect(public_home_link).to_be_visible()
    public_home_link.click()
    
    expect(page.get_by_test_id("public-sign-out")).to_be_visible(timeout=10000)

    # Click sign out (from public page)
    page.get_by_test_id("public-sign-out").click()

    # Ensure redirection to sign-in page (login button should be visible)
    expect(page.get_by_role("button", name="Login")).to_be_visible(timeout=10000) # Corrected selector
    expect(page.get_by_text("This login form is for demonstration purposes only")).to_be_visible(timeout=5000)
