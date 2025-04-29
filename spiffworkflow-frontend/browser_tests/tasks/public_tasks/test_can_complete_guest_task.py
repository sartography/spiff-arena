import os
import pytest
from playwright.sync_api import expect

from helpers.login import login, logout, BASE_URL
from helpers.playwright_setup import browser_context  # fixture


def test_can_complete_guest_task(browser_context):
    """Tests that a guest task can be completed via the public link and link cannot be reused."""
    page = browser_context.new_page()

    # 1. Log in and start the guest task process
    login(page, "admin", "admin")
    # Navigate to process groups
    page.goto(f"{BASE_URL}/process-groups")
    # Select the 'Shared Resources' group
    page.get_by_text("Shared Resources", exact=False).first.click()
    expect(page.get_by_test_id("process-group-breadcrumb-Shared Resources")).to_be_visible()

    # Select the process model with guest task
    model_name = "task-with-guest-form"
    page.get_by_test_id(f"process-model-card-{model_name}").first.click()
    expect(page.get_by_text(f"Process Model: {model_name}", exact=False)).to_be_visible()

    # Start the process instance; metadata should appear on this page
    page.get_by_test_id("start-process-instance").first.click()

    # 2. Extract the public guest task link from metadata
    link_locator = page.locator('[data-testid="metadata-value-first_task_url"] a')
    expect(link_locator).to_be_visible(timeout=15000)
    task_link = link_locator.get_attribute("href")
    assert task_link, "Expected guest task link in metadata"

    # 3. Log out of the application
    logout(page)

    # 4. Visit the public guest task URL and complete both forms as a guest
    page.goto(task_link)
    # First guest form submission
    page.get_by_text("Submit", exact=True).click()
    # Second guest form submission
    page.get_by_text("Submit", exact=True).click()
    # Confirm completion message
    expect(page.get_by_text("You are done. Yay!", exact=False)).to_be_visible()

    # 5. Verify the link cannot be reused
    page.goto(task_link)
    expect(page.get_by_text("Error retrieving content.", exact=False)).to_be_visible()

    # 6. Click public home link, sign out, and ensure redirection to sign-in or login button
    page.get_by_test_id("public-home-link").click()
    page.get_by_test_id("public-sign-out").click()
    if os.environ.get("SPIFFWORKFLOW_FRONTEND_AUTH_WITH_KEYCLOAK", "false").lower() == "true":
        expect(page.get_by_text("Sign in to your account", exact=False)).to_be_visible()
    else:
        expect(page.locator("#spiff-login-button")).to_be_visible()
