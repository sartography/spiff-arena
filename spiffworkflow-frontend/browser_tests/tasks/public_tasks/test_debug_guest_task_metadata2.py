import pytest
from playwright.sync_api import expect

from helpers.login import login, BASE_URL
from helpers.debug import print_page_details
from helpers.playwright_setup import browser_context  # fixture


def test_debug_guest_task_metadata2(browser_context):
    """Debug metadata presence on interstitial interstitial page after starting guest task."""
    page = browser_context.new_page()
    # 1. Log in and navigate to process model
    login(page, "admin", "admin")
    page.goto(f"{BASE_URL}/process-groups")
    page.get_by_text("Shared Resources", exact=False).first.click()
    expect(page.get_by_test_id("process-group-breadcrumb-Shared Resources")).to_be_visible()
    model_name = "task-with-guest-form"
    page.get_by_test_id(f"process-model-card-{model_name}").first.click()
    expect(page.get_by_text(f"Process Model: {model_name}", exact=False)).to_be_visible()
    # 2. Start process without waiting for navigation
    page.get_by_test_id("start-process-instance").first.click(no_wait_after=True)
    # Wait for metadata link
    selector = '[data-testid="metadata-value-first_task_url"] a'
    element = page.wait_for_selector(selector, timeout=20000)
    print("DEBUG URL ->", page.url)
    print_page_details(page)
    href = element.get_attribute("href")
    print("DEBUG href ->", href)
    pytest.skip("debug metadata complete")
