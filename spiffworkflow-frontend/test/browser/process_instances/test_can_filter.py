import re
import pytest
from datetime import datetime, timedelta
from playwright.sync_api import expect, Page

from helpers.login import login, logout, BASE_URL
from helpers.debug import print_page_details


def titleize(status: str) -> str:
    """Convert status string like 'not_started' to 'Not Started'."""
    return " ".join([word.capitalize() for word in status.split("_")])


def test_can_filter(page: Page):
    """
    Test that users can filter process instances by status and date, and see correct filtered results.
    """

    # 1. Log in
    login(page)

    # 2. Create a fresh process instance to ensure a recent date entry
    page.goto(f"{BASE_URL}/process-groups")
    page.get_by_text("Shared Resources", exact=False).first.click()
    expect(page.get_by_test_id("process-group-breadcrumb-Shared Resources")).to_be_visible()
    page.get_by_text("Acceptance Tests Group One", exact=False).first.click()
    expect(page.get_by_test_id("process-group-breadcrumb-Acceptance Tests Group One")).to_be_visible()
    model_name = "Acceptance Tests Model 1"
    page.get_by_test_id(f"process-model-card-{model_name}").first.click()
    expect(page.get_by_text(f"Process Model: {model_name}", exact=False)).to_be_visible()
    start_btn = page.get_by_test_id("start-process-instance").first
    expect(start_btn).to_be_enabled(timeout=10000)
    start_btn.click()
    # Wait for navigation to process-instances
    page.wait_for_url(re.compile(r"/process-instances"), timeout=10000)

    # 3. Navigate to the all instances list
    page.goto(f"{BASE_URL}/process-instances/all")
    expect(page.get_by_text("All Process Instances", exact=False)).to_be_visible(timeout=10000)

    # Locator for result items
    item_locator = page.get_by_test_id("process-instance-show-link-id")
    # Ensure at least one item exists
    expect(item_locator.first).to_be_visible(timeout=10000)

    # 4. Expand filter section
    page.get_by_test_id("filter-section-expand-toggle").click()

    # 5. Filter by each status except 'all' and 'waiting', verifying UI tag behavior
    statuses = [
        "complete", "error", "not_started", "running",
        "suspended", "terminated", "user_input_required",
    ]
    for status in statuses:
        # Open status dropdown and select the status
        select = page.locator("#process-instance-status-select")
        select.click()
        select.get_by_text(titleize(status), exact=False).click()
        # After selection, a tag '1' appears
        tag = page.locator("#process-instance-status-select .cds--tag", has_text="1")
        expect(tag).to_be_visible(timeout=5000)
        # Clear the status filter
        clear_btn = page.locator('div[aria-label="Clear all selected items"]').first
        clear_btn.click()
        # Confirm tag removed
        expect(page.locator("#process-instance-status-select .cds--tag")).to_have_count(0)

    # 6. Filter by a recent past date (1 hour ago) and expect results
    past = datetime.now() - timedelta(hours=1)
    page.locator("#date-picker-start-from").fill(past.strftime("%Y-%m-%d"))
    page.get_by_text("Start date to", exact=False).click()
    page.locator("#time-picker-start-from").fill(past.strftime("%H:%M"))
    page.locator("#date-picker-end-from").fill(past.strftime("%Y-%m-%d"))
    page.get_by_text("End date to", exact=False).click()
    page.locator("#time-picker-end-from").fill(past.strftime("%H:%M"))
    # Click header to apply filter
    page.get_by_text("All Process Instances", exact=False).click()
    page.wait_for_timeout(500)
    # Debugging if no results
    if item_locator.count() == 0:
        print_page_details(page)
    count_past = item_locator.count()
    assert count_past > 0, f"Expected some process instances for past date, got {count_past}"

    # 7. Filter by a future date (26h ahead) and expect no results
    future = datetime.now() + timedelta(hours=26)
    page.locator("#date-picker-start-from").fill(future.strftime("%Y-%m-%d"))
    page.get_by_text("Start date to", exact=False).click()
    page.locator("#time-picker-start-from").fill(future.strftime("%H:%M"))
    page.locator("#date-picker-end-from").fill(future.strftime("%Y-%m-%d"))
    page.get_by_text("End date to", exact=False).click()
    page.locator("#time-picker-end-from").fill(future.strftime("%H:%M"))
    # Click header to apply filter
    page.get_by_text("All Process Instances", exact=False).click()
    page.wait_for_timeout(500)
    count_future = item_locator.count()
    assert count_future == 0, f"Expected no process instances for future date, got {count_future}"

    # 8. Cleanup: logout
    logout(page)
