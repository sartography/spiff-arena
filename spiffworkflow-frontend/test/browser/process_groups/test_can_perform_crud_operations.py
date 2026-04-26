import uuid
import re
from playwright.sync_api import expect, Page

from helpers.login import login, logout, BASE_URL
from helpers.debug import print_page_details


def test_can_perform_crud_operations(page: Page):
    """
    Test that a user can create, view, update, and delete a process group via the UI.
    """

    # 1. Log in
    login(page)

    # 2. Navigate to process groups list
    list_url = f"{BASE_URL}/process-groups"
    page.goto(list_url)

    # 3. Create a new process group
    unique = uuid.uuid4().hex
    group_id = f"test-group-{unique}"
    group_name = f"Test Group {unique}"
    updated_name = f"{group_name} edited"

    print_page_details(page)
    # Open the creation form.
    # We wait for the specific "new" link to appear, which is more robust
    # than the previous implementation that didn't wait correctly.
    add_button_locator = page.locator(
        'a[data-testid="add-process-group-button"][href*="/process-groups/"][href$="/new"]'
    )
    expect(add_button_locator).to_be_visible(timeout=20000)
    add_button_locator.click()
    print_page_details(page)  # print immediately after click for debug

    # Try to robustly detect the form page for new group
    if not re.search(r"/process-groups/new$", page.url):
        print("[DEBUG] Unexpected URL after clicking add-process-group-button!")
        print_page_details(page)
        page.goto(f"{BASE_URL}/process-groups/new")
        print_page_details(page)
        expect(page).to_have_url(re.compile(r"/process-groups/new$"), timeout=10000)

    # Fill in the creation form
    display_input = page.locator('#process-group-display-name')
    expect(display_input).to_be_visible()
    display_input.fill(group_name)
    expect(display_input).to_have_value(group_name)

    id_input = page.locator('#process-group-identifier')
    expect(id_input).to_be_visible()
    id_input.fill(group_id)
    expect(id_input).to_have_value(group_id)

    # Submit the form
    submit_btn = page.get_by_role("button", name="Submit")
    expect(submit_btn).to_be_enabled()
    submit_btn.click()

    # 4. Verify detail page loaded with correct group
    expect(page).to_have_url(re.compile(fr"/process-groups/{group_id}$"), timeout=10000)
    print_page_details(page)
    # Instead of get_by_text, just check the breadcrumb (matches detail page)
    bread_crumb_selector = f'[data-testid="process-group-breadcrumb-{group_name}"]'
    bread_crumb = page.locator(bread_crumb_selector)
    expect(bread_crumb).to_be_visible()

    # 5. Update the process group display name
    edit_btn = page.get_by_test_id("edit-process-group-button")
    expect(edit_btn).to_be_visible()
    edit_btn.click()
    expect(page).to_have_url(re.compile(fr"/process-groups/{group_id}/edit$"), timeout=10000)
    print_page_details(page)

    # Fill in the update form
    edit_input = page.locator('#process-group-display-name')
    expect(edit_input).to_be_visible()
    edit_input.fill(updated_name)
    expect(edit_input).to_have_value(updated_name)

    # Submit the update
    update_btn = page.get_by_role("button", name="Submit")
    expect(update_btn).to_be_enabled()
    update_btn.click()

    # Confirm updated detail page
    expect(page).to_have_url(re.compile(fr"/process-groups/{group_id}$"), timeout=10000)
    print_page_details(page)
    # Check updated breadcrumb
    bread_crumb_selector = f'[data-testid="process-group-breadcrumb-{updated_name}"]'
    bread_crumb = page.locator(bread_crumb_selector)
    expect(bread_crumb).to_be_visible()

    # 6. Delete the process group
    delete_btn = page.get_by_test_id("delete-process-group-button")
    expect(delete_btn).to_be_visible()
    delete_btn.click()

    # Wait for matching modal, get all dialogs and locate Delete button
    dialogs = page.get_by_role('dialog')
    expect(dialogs).to_be_visible(timeout=10000)
    print_page_details(page)
    # There may be multiple dialogs, but only one with a visible 'Delete' button
    delete_btns = dialogs.locator('button', has_text='Delete')
    count = delete_btns.count()
    found = False
    for i in range(count):
        btn = delete_btns.nth(i)
        if btn.is_visible():
            btn.click()
            found = True
            break
    if not found:
        print("[DEBUG] Could not find visible Delete button in dialog!")
        print_page_details(page)
        assert False, 'Delete button for modal not found'

    # 7. Verify deletion: back to list, group no longer appears
    expect(page).to_have_url(re.compile(r"/process-groups$"), timeout=10000)
    print_page_details(page)
    not_found = page.locator(f'[data-testid="process-group-breadcrumb-{updated_name}"]')
    expect(not_found).to_have_count(0)

    # 8. Log out
    logout(page)
