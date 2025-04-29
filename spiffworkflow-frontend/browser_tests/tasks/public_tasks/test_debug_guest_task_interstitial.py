import pytest
from playwright.sync_api import expect

from helpers.login import login, BASE_URL
from helpers.debug import print_page_details
from helpers.playwright_setup import browser_context  # fixture


def test_debug_guest_task_interstitial(browser_context):
    """Debug the metadata interstitial page after starting guest task process."""
    page = browser_context.new_page()
    # 1. Log in and navigate to the guest task process model
    login(page, "admin", "admin")
    page.goto(f"{BASE_URL}/process-groups")
    page.get_by_text("Shared Resources", exact=False).first.click()
    expect(page.get_by_test_id("process-group-breadcrumb-Shared Resources")).to_be_visible()
    model_name = "task-with-guest-form"
    page.get_by_test_id(f"process-model-card-{model_name}").first.click()
    expect(page.get_by_text(f"Process Model: {model_name}", exact=False)).to_be_visible()
    # 2. Start process instance
    page.get_by_test_id("start-process-instance").first.click()
    # Wait for interstitial page where metadata is displayed
    page.wait_for_url("**/interstitial", timeout=20000)
    print("DEBUG INTERSTITIAL URL:", page.url)
    print_page_details(page)
    pytest.skip("debug guest task interstitial complete")