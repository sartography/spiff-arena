import pytest
from playwright.sync_api import expect

from helpers.login import login, BASE_URL
from helpers.playwright_setup import browser_context  # fixture
from helpers.debug import print_page_details


def test_debug_metadata_show_page(browser_context):
    page = browser_context.new_page()
    # 1. Login and start process
    login(page, "admin", "admin")
    page.goto(f"{BASE_URL}/process-groups")
    page.get_by_text("Shared Resources", exact=False).first.click()
    page.get_by_test_id("process-group-breadcrumb-Shared Resources").wait_for(timeout=10000)
    model_name = "task-with-guest-form"
    page.get_by_test_id(f"process-model-card-{model_name}").first.click()
    page.get_by_text(f"Process Model: {model_name}", exact=False).wait_for(timeout=10000)
    page.get_by_test_id("start-process-instance").first.click()

    # 2. Go to instance list for this model
    page.get_by_test_id("process-instance-list-link").first.click()
    # Wait for table rows
    page.locator("tbody tr").first.wait_for(timeout=10000)

    # 3. Open instance show page
    page.get_by_test_id("process-instance-show-link-id").first.click()
    # Wait for navigation to show page
    page.wait_for_url("**/process-instances/*", timeout=10000)

    # 4. Debug: print URL and page details
    print("DEBUG SHOW URL ->", page.url)
    print_page_details(page)
    pytest.skip("debug complete")
