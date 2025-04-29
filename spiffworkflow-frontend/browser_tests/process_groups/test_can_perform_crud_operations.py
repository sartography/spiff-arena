import uuid
import re
from playwright.sync_api import expect, BrowserContext

from helpers.login import login, logout, BASE_URL
from helpers.playwright_setup import browser_context  # fixture


def test_can_perform_crud_operations(browser_context: BrowserContext):
    """
    Test that a user can create, view, update, and delete a process group via the UI.
    """
    page = browser_context.new_page()

    # 1. Log in
    login(page, "admin", "admin")

    # 2. Navigate to process groups list
    list_url = f"{BASE_URL}/process-groups"
    page.goto(list_url)

    # 3. Create a new process group
    unique = uuid.uuid4().hex
    group_id = f"test-group-{unique}"
    group_name = f"Test Group {unique}"
    updated_name = f"{group_name} edited"

    # Open the creation form
    add_btn = page.get_by_test_id("add-process-group-button")
    expect(add_btn).to_be_visible(timeout=10000)
    add_btn.click()
    expect(page).to_have_url(re.compile(r"/process-groups/new$"), timeout=10000)

    # Fill in the creation form
    display_input = page.get_by_label("Display Name*")
    expect(display_input).to_be_visible()
    display_input.fill(group_name)
    expect(display_input).to_have_value(group_name)

    id_input = page.get_by_label("Identifier*")
    expect(id_input).to_be_visible()
    id_input.fill(group_id)
    expect(id_input).to_have_value(group_id)

    # Submit the form
    submit_btn = page.get_by_role("button", name="Submit")
    expect(submit_btn).to_be_enabled()
    submit_btn.click()

    # 4. Verify detail page loaded with correct group
    expect(page).to_have_url(re.compile(fr"/process-groups/{group_id}$"), timeout=10000)
    expect(page.get_by_text(f"Process Group: {group_name}")).to_be_visible()

    # 5. Update the process group display name
    edit_btn = page.get_by_test_id("edit-process-group-button")
    expect(edit_btn).to_be_visible()
    edit_btn.click()
    expect(page).to_have_url(re.compile(fr"/process-groups/{group_id}/edit$"), timeout=10000)

    # Fill in the update form
    edit_input = page.get_by_label("Display Name*")
    expect(edit_input).to_be_visible()
    edit_input.fill(updated_name)
    expect(edit_input).to_have_value(updated_name)

    # Submit the update
    update_btn = page.get_by_role("button", name="Submit")
    expect(update_btn).to_be_enabled()
    update_btn.click()

    # Confirm updated detail page
    expect(page).to_have_url(re.compile(fr"/process-groups/{group_id}$"), timeout=10000)
    expect(page.get_by_text(f"Process Group: {updated_name}")).to_be_visible()

    # 6. Delete the process group
    delete_btn = page.get_by_test_id("delete-process-group-button")
    expect(delete_btn).to_be_visible()
    delete_btn.click()

    # Confirm deletion in modal
    confirm_modal = page.get_by_test_id("delete-process-group-button-modal-confirmation-dialog")
    expect(confirm_modal).to_be_visible(timeout=10000)
    # Click the destructive confirm button
    confirm_modal.locator(".cds--btn--danger").click()

    # 7. Verify deletion: back to list, group no longer appears
    expect(page).to_have_url(re.compile(r"/process-groups$"), timeout=10000)
    expect(page.get_by_text(updated_name)).to_have_count(0)

    # 8. Log out
    logout(page)
