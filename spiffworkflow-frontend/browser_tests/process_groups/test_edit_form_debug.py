import uuid
from playwright.sync_api import BrowserContext
from helpers.login import login, logout, BASE_URL
from helpers.playwright_setup import browser_context
from helpers.debug import print_page_details

def test_edit_form_debug(browser_context: BrowserContext):
    page = browser_context.new_page()
    login(page, "admin", "admin")
    # Create new group
    unique = uuid.uuid4().hex
    group_id = f"test-group-{unique}"
    group_name = f"Test Group {unique}"
    # Navigate to new form
    page.goto(f"{BASE_URL}/process-groups/new")
    # Fill and submit creation form
    page.locator('#process-group-display-name').fill(group_name)
    page.locator('#process-group-identifier').fill(group_id)
    page.get_by_role('button', name='Submit').click()
    # Wait for detail
    page.wait_for_url(f"{BASE_URL}/process-groups/{group_id}")
    # Print details before edit
    print_page_details(page)
    # Click edit
    page.get_by_test_id('edit-process-group-button').click()
    page.wait_for_url(f"{BASE_URL}/process-groups/{group_id}/edit")
    page.wait_for_load_state()
    # Print details in edit form
    print_page_details(page)
    assert False, 'stop'