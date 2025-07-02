import re
from playwright.sync_api import expect, BrowserContext

from helpers.login import login, logout, BASE_URL
from helpers.playwright_setup import browser_context  # fixture
from helpers.debug import print_page_details


def test_can_display_logs(browser_context: BrowserContext):
    """
    Test that process instance logs are displayed and paginated correctly.
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

    model_url = page.url

    # 3. Run a process instance to ensure one exists
    start_btn = page.get_by_test_id("start-process-instance").first
    expect(start_btn).to_be_enabled(timeout=10000)
    start_btn.click()
    # Wait for navigation to process instances list
    page.wait_for_url(re.compile(r"/process-instances"), timeout=10000)

    # 4. Return to model page to access list tab
    page.goto(model_url)
    page.wait_for_url(model_url, timeout=10000)

    # 5. Open the process instance list tab
    page.get_by_test_id("process-instance-list-link").click()
    # Wait for the first instance entry to be visible
    expect(page.get_by_test_id("process-instance-show-link-id").first).to_be_visible(timeout=10000)

    # 6. Open the first instance's details
    page.get_by_test_id("process-instance-show-link-id").first.click()

    # 7. Go to the 'Events' tab
    page.get_by_text("Events", exact=False).click()

    # Debug: print test IDs and interactable elements to assist with selectors
    print_page_details(page)

    # 8. Confirm presence of key log/event outputs
    expect(page.get_by_text("process_model_one").first).to_be_visible(timeout=5000)
    expect(page.get_by_text("task_completed").first).to_be_visible(timeout=5000)

    # 9. Confirm pagination controls for events exist
    prev_button = page.get_by_role("button", name="Go to previous page")
    next_button = page.get_by_role("button", name="Go to next page")
    expect(prev_button).to_be_visible()
    expect(next_button).to_be_visible()

    # Cleanup: logout
    logout(page)
