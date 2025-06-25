import re
import pytest
from playwright.sync_api import expect, BrowserContext

from helpers.login import login, logout, BASE_URL
from helpers.playwright_setup import browser_context  # fixture
from helpers.debug import print_page_details


def test_can_paginate_items(browser_context: BrowserContext):
    """
    Test that process instance list supports pagination controls (forward/backward paging).
    """
    page = browser_context.new_page()

    # 1. Log in
    login(page, "admin", "admin")

    # 2. Navigate to the process model show page
    page.goto(f"{BASE_URL}/process-groups")
    page.get_by_text("Shared Resources", exact=False).first.click()
    expect(page.get_by_test_id("process-group-breadcrumb-Shared Resources")).to_be_visible()
    page.get_by_text("Acceptance Tests Group One", exact=False).first.click()
    expect(page.get_by_test_id("process-group-breadcrumb-Acceptance Tests Group One")).to_be_visible()
    model_name = "Acceptance Tests Model 1"
    page.get_by_test_id(f"process-model-card-{model_name}").first.click()
    expect(page.get_by_text(f"Process Model: {model_name}", exact=False)).to_be_visible()

    # 3. Create multiple process instances by clicking Start and returning to model page
    model_url = page.url
    for _ in range(5):
        start_btn = page.get_by_test_id("start-process-instance").first
        expect(start_btn).to_be_enabled(timeout=10000)
        start_btn.click()
        page.wait_for_url(re.compile(r"/process-instances"), timeout=10000)
        page.goto(model_url)
        page.wait_for_url(model_url, timeout=10000)
        expect(page.get_by_test_id("start-process-instance")).to_be_visible(timeout=10000)

    # 4. Open the process instance list tab
    page.get_by_test_id("process-instance-list-link").click()
    # Debug: print page details to inspect pagination controls
    print_page_details(page)

    # 5. Perform pagination test: set items per page to 2
    pagination = page.get_by_test_id("pagination-options")
    pagination.scroll_into_view_if_needed()
    # ??? further code to follow
    # 6. Logout (cleanup)
    logout(page)
