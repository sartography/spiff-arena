import os
from playwright.sync_api import expect

from helpers.login import login, logout, BASE_URL
from helpers.playwright_setup import browser_context  # fixture

def test_can_complete_guest_task(browser_context):
    """Tests that a guest task can be completed via the public link and link cannot be reused."""
    page = browser_context.new_page()

    # 1. Log in and navigate to the 'Shared Resources' process model
    login(page, "admin", "admin")
    page.goto(f"{BASE_URL}/process-groups")
    page.get_by_text("Shared Resources", exact=False).first.click()

    # Open the process model details
    model_name = "task-with-guest-form"
    page.get_by_test_id(f"process-model-card-{model_name}").first.click()
    expect(page.get_by_text(f"Process Model: {model_name}", exact=False)).to_be_visible()

    # 2. Start the process instance; metadata appears below
    page.get_by_test_id("start-process-instance").first.click()

    # 3. Extract the public guest task link from metadata field
    link_locator = page.get_by_test_id("metadata-value-first_task_url").locator("a")
    expect(link_locator).to_be_visible(timeout=15000)
    task_link = link_locator.get_attribute("href")
    assert task_link, "Expected guest task link in metadata"

    # 4. Log out of the authenticated session
    logout(page)

    # 5. Visit the public guest task URL as a guest and complete both forms
    page.goto(task_link)
    page.get_by_role("button", name="Submit").click()
    page.get_by_role("button", name="Submit").click()
    expect(page.get_by_text("You are done. Yay!", exact=False)).to_be_visible()

    # 6. Verify the link cannot be reused
    page.goto(task_link)
    expect(page.get_by_text("Error retrieving content.", exact=False)).to_be_visible()

    # 7. Public navigation: home and sign out
    page.get_by_test_id("public-home-link").click()
    page.get_by_test_id("public-sign-out").click()
    # Check redirection to sign-in or presence of login button
    if os.environ.get("SPIFFWORKFLOW_FRONTEND_AUTH_WITH_KEYCLOAK", "false").lower() == "true":
        expect(page.get_by_text("Sign in to your account", exact=False)).to_be_visible()
    else:
        expect(page.locator("#spiff-login-button")).to_be_visible()
