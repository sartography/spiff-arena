import re
from datetime import datetime, timedelta
from playwright.sync_api import expect, Page

from helpers.login import login, logout, BASE_URL
from helpers.debug import print_page_details
from helpers.process_groups import switch_to_card_view


def titleize(status: str) -> str:
    """Convert status string like 'not_started' to 'Not Started'."""
    return " ".join([word.capitalize() for word in status.split("_")])


def select_calendar_date(page: Page, date: datetime):
    calendar = page.get_by_test_id("absolute-time-range-picker")
    target_month = date.strftime("%B %Y")
    month_header = calendar.locator(".react-datepicker__current-month")
    for _ in range(3):
        if month_header.inner_text() == target_month:
            break
        calendar.get_by_role("button", name="Next Month").click()
    else:
        raise AssertionError(f"Could not navigate calendar to {target_month}")

    day = calendar.locator(
        ".react-datepicker__day:not(.react-datepicker__day--outside-month)"
    ).filter(has_text=re.compile(rf"^{date.day}$"))
    expect(day).to_have_count(1)
    day.click()


def test_can_filter(page: Page):
    """
    Test that users can filter process instances by status and date, and see correct filtered results.
    """

    # 1. Log in
    login(page)

    # 2. Create a fresh process instance to ensure a recent date entry
    page.goto(f"{BASE_URL}/process-groups")
    switch_to_card_view(page)
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

    first_column_chip = page.locator(".filter-tag").first
    expect(first_column_chip).to_be_visible()
    assert first_column_chip.bounding_box()["width"] <= 128

    save_button = page.get_by_role("button", name="Save", exact=True)
    clear_filters_button = page.get_by_role("button", name="Clear", exact=True)
    advanced_button = page.get_by_test_id("advanced-options-filters")
    expect(save_button).to_be_visible()
    expect(clear_filters_button).to_be_visible()
    expect(advanced_button).to_be_visible()
    assert save_button.bounding_box()["x"] < clear_filters_button.bounding_box()["x"]
    assert advanced_button.bounding_box()["x"] > clear_filters_button.bounding_box()["x"]

    # 5. Filter by each status except 'all' and 'waiting', verifying UI tag behavior
    statuses = [
        "complete", "error", "not_started", "running",
        "suspended", "terminated", "user_input_required",
    ]
    for status in statuses:
        # Open status dropdown and select the status
        select = page.locator("#process-instance-status-select")
        select.click()
        page.get_by_role("option", name=titleize(status), exact=True).click()
        # After selection, a chip for the selected status appears
        tag = page.locator(".MuiAutocomplete-tag")
        expect(tag).to_be_visible(timeout=5000)
        expect(tag).to_contain_text(titleize(status))
        # Clear the status filter
        status_autocomplete = select.locator(
            "xpath=ancestor::div[contains(@class, 'MuiAutocomplete-root')]"
        )
        clear_btn = status_autocomplete.get_by_title("Clear")
        clear_btn.click()
        # Confirm chip removed
        expect(page.locator(".MuiAutocomplete-tag")).to_have_count(0)

    # 6. Filter to instances started in the last hour and expect results
    time_range_button = page.get_by_test_id("time-range-filter-button")
    time_range_button.click()
    page.get_by_role("menuitem", name="Last hour").click()
    expect(time_range_button).to_contain_text("1H")
    # Debugging if no results
    if item_locator.count() == 0:
        print_page_details(page)
    count_past = item_locator.count()
    assert count_past > 0, f"Expected some process instances for past date, got {count_past}"

    # 7. Filter by an absolute future range and expect no results
    future_start = datetime.now() + timedelta(hours=26)
    future_end = future_start + timedelta(days=1)
    time_range_button.click()
    page.get_by_role("menuitem", name="Absolute date").click()
    select_calendar_date(page, future_start)
    select_calendar_date(page, future_end)
    page.get_by_label("Start time").fill(future_start.strftime("%H:%M"))
    page.get_by_label("End time").fill(future_end.strftime("%H:%M"))
    page.get_by_role("button", name="Apply").click()
    expect(item_locator).to_have_count(0, timeout=10000)

    # 8. Cleanup: logout
    logout(page)
