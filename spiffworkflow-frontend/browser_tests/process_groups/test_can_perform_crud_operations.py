import pytest
import re
from playwright.sync_api import Page, expect
from uuid import uuid4
# Assuming helpers are now relative to the tests directory root
from ..helpers.login import login, logout

# Removed inline login and logout functions, will use imported helpers

def create_group(page: Page, group_id: str, group_display_name: str):
    # Navigate to process groups page before creating
    page.goto("http://localhost:7001/process-groups")
    expect(page.locator('[data-testid=process-groups-loaded]')).to_be_visible()
    # Check if group already exists (optional, depends on test needs)
    # assert not page.locator(f'text={group_id}').is_visible() # This might fail if test reruns without cleanup
    page.click('text=Add a process group')
    page.fill('input[name=display_name]', group_display_name)
    expect(page.locator('input[name=display_name]')).to_have_value(group_display_name)
    expect(page.locator('input[name=id]')).to_have_value(group_id)
    page.click('text=Submit')
    page.wait_for_url(re.compile(f'.*process-groups/{group_id}'))
    expect(page.locator(f'text=Process Group: {group_display_name}')).to_be_visible()

@pytest.mark.order(1)
def test_can_perform_crud_operations(page: Page):
    # Use imported login helper
    login(page, "admin", "admin")
    unique = str(uuid4())[:8]
    group_id = f"test-group-1-{unique}"
    group_display_name = f"Test Group 1 {unique}"
    new_group_display_name = f"{group_display_name} edited"

    # Create Group
    create_group(page, group_id, group_display_name)

    # Go back to Process Groups list (if needed)
    page.click('text=Process Groups')
    page.click(f'text={group_display_name}')
    expect(page).to_have_url(re.compile(f'.*process-groups/{group_id}'))
    expect(page.locator(f'text=Process Group: {group_display_name}')).to_be_visible()

    # Edit Group
    page.click('[data-testid=edit-process-group-button]')
    page.wait_for_selector('[data-testid=process-group-display-name-input]')
    page.fill('[data-testid=process-group-display-name-input]', new_group_display_name)
    page.click('text=Submit')
    expect(page.locator(f'text=Process Group: {new_group_display_name}')).to_be_visible()

    # Delete Group
    page.click('[data-testid=delete-process-group-button]')
    expect(page.locator('text=Are you sure')).to_be_visible()
    modal = page.locator('[data-testid=delete-process-group-button-modal-confirmation-dialog]')
    modal.locator('.cds--btn--danger').click()
    expect(page).to_have_url(re.compile(r'.*/process-groups($|\?)'))
    expect(page.locator(f'text={new_group_display_name}')).not_to_be_visible()
    expect(page.locator('[data-testid=process-groups-loaded]')).to_be_visible()

    # Use imported logout helper
    logout(page)
