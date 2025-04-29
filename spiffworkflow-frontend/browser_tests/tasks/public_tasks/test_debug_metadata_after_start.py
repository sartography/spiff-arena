import pytest
from playwright.sync_api import Page

from helpers.login import login, BASE_URL
from helpers.playwright_setup import browser_context  # fixture
from helpers.debug import print_page_details


def test_debug_metadata_after_start(browser_context: browser_context):
    page = browser_context.new_page()
    # 1. Log in and start the guest task process
    login(page, "admin", "admin")
    page.goto(f"{BASE_URL}/process-groups")
    page.get_by_text("Shared Resources", exact=False).first.click()
    page.get_by_test_id("process-group-breadcrumb-Shared Resources").wait_for(timeout=10000)
    model_name = "task-with-guest-form"
    page.get_by_test_id(f"process-model-card-{model_name}").first.click()
    page.get_by_text(f"Process Model: {model_name}", exact=False).wait_for(timeout=10000)
    # Start the process instance
    page.get_by_test_id("start-process-instance").first.click()

    # Wait for the metadata panel to load
    page.wait_for_timeout(2000)
    print("DEBUG URL:", page.url)
    print_page_details(page)
    pytest.skip("Debug metadata after start complete")
