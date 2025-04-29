import pytest
from playwright.sync_api import Page

from helpers.login import login, BASE_URL
from helpers.playwright_setup import browser_context  # fixture
from helpers.debug import print_page_details


def test_debug_instance_show(browser_context):
    """Debug test to inspect process instance show page elements for metadata."""
    page = browser_context.new_page()
    # 1. Login and start the guest task process
    login(page, "admin", "admin")
    page.goto(f"{BASE_URL}/process-groups")
    # Select the Shared Resources group
    page.get_by_text("Shared Resources", exact=False).first.click()
    page.get_by_test_id("process-group-breadcrumb-Shared Resources").wait_for(timeout=10000)
    # Select the specific process model
    model_name = "task-with-guest-form"
    page.get_by_test_id(f"process-model-card-{model_name}").first.click()
    page.get_by_text(f"Process Model: {model_name}", exact=False).wait_for(timeout=10000)
    # Start the process instance
    page.get_by_test_id("start-process-instance").first.click()

    # 2. Go to the process instance list and open the first instance
    page.get_by_test_id("process-instance-list-link").first.click()
    page.locator("tbody tr").first.wait_for(timeout=10000)
    page.get_by_test_id("process-instance-show-link-id").first.click()
    # Wait for the instance show page URL
    page.wait_for_url("**/process-instances/*", timeout=10000)

    # Debug: print page details
    print("DEBUG SHOW URL ->", page.url)
    print_page_details(page)

    pytest.skip("Debug inspection of instance show page complete")
