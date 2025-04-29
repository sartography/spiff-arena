import uuid
from playwright.sync_api import BrowserContext

from helpers.login import login, BASE_URL
from helpers.playwright_setup import browser_context
from helpers.debug import print_page_details

def test_process_group_detail_debug(browser_context: BrowserContext):
    page = browser_context.new_page()
    login(page, "admin", "admin")
    # Navigate to creation page
    page.goto(f"{BASE_URL}/process-groups/new")
    unique = uuid.uuid4().hex
    group_id = f"test-group-{unique}"
    group_display_name = f"Test Group {unique}"
    # Fill and submit
    page.locator('#process-group-display-name').fill(group_display_name)
    # Assume id auto-filled, no need to fill
    page.get_by_role('button', name='Submit').click()
    # Wait for navigation
    page.wait_for_url(f"{BASE_URL}/process-groups/{group_id}", timeout=10000)
    # Print page details
    print_page_details(page)
    # Inspect header location
    # Fail to inspect
    assert False, "Debug detail page"
