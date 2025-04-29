import pytest
from playwright.sync_api import expect

from helpers.login import login, BASE_URL
from helpers.debug import print_page_details
from helpers.playwright_setup import browser_context  # fixture


def test_debug_guest_task_metadata(browser_context):
    """Debug the interstitial metadata page after starting a guest task process."""
    page = browser_context.new_page()
    # 1. Log in
    login(page, "admin", "admin")
    # Navigate to process groups and select group
    page.goto(f"{BASE_URL}/process-groups")
    page.get_by_text("Shared Resources", exact=False).first.click()
    expect(page.get_by_test_id("process-group-breadcrumb-Shared Resources")).to_be_visible()
    # 2. Select model
    model_name = "task-with-guest-form"
    page.get_by_test_id(f"process-model-card-{model_name}").first.click()
    expect(page.get_by_text(f"Process Model: {model_name}", exact=False)).to_be_visible()
    # 3. Start process and debug
    page.get_by_test_id("start-process-instance").first.click(no_wait_after=True)
    # Wait for interstitial
    page.wait_for_url("**/process-instances/*/interstitial", timeout=15000)
    print("DEBUG URL:", page.url)
    print_page_details(page)
    pytest.skip("Debug metadata complete")
