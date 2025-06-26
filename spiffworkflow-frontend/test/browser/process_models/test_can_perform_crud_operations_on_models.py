import uuid
import re
from playwright.sync_api import expect, BrowserContext

from helpers.login import login, logout, BASE_URL
from helpers.playwright_setup import browser_context  # fixture


def test_can_perform_crud_operations_on_models(browser_context: BrowserContext):
    """
    Test that a user can create, view, update, and delete a process model via the UI.
    """
    page = browser_context.new_page()

    # 1. Log in
    login(page, "admin", "admin")

    # 2. Navigate to the specific process group page
    group_id = "misc/acceptance-tests-group-one"
    group_path = group_id.replace("/", ":")  # URL uses ':' to separate namespace
    page.goto(f"{BASE_URL}/process-groups/{group_path}")

    # Confirm on group page via breadcrumbs
    expect(
        page.get_by_test_id("process-group-breadcrumb-Shared Resources")
    ).to_be_visible(timeout=10000)
    expect(
        page.get_by_test_id("process-group-breadcrumb-Acceptance Tests Group One")
    ).to_be_visible(timeout=10000)

    # 3. Create a new process model
    unique = uuid.uuid4().hex
    model_id = f"test-model-{unique}"
    display_name = f"Test Model {unique}"

    # Open creation form
    add_btn = page.get_by_test_id("add-process-model-button")
    expect(add_btn).to_be_visible(timeout=10000)
    add_btn.click()

    # Verify navigation to new model form
    expect(page).to_have_url(
        re.compile(rf".*/process-models/{re.escape(group_path)}/new$"),
        timeout=10000,
    )

    # Fill in creation form
    display_input = page.locator('input[name="display_name"]')
    expect(display_input).to_be_visible()
    display_input.fill(display_name)
    expect(display_input).to_have_value(display_name)

    id_input = page.locator('input[name="id"]')
    expect(id_input).to_be_visible()
    id_input.fill(model_id)
    expect(id_input).to_have_value(model_id)

    # Submit the form
    submit_btn = page.get_by_role("button", name="Submit")
    expect(submit_btn).to_be_enabled()
    submit_btn.click()

    # 4. Verify detail page loaded with correct model
    # URL pattern: /process-models/{group_path}:{model_id}
    expect(page).to_have_url(
        re.compile(
            rf".*/process-models/{re.escape(group_path)}:{re.escape(model_id)}$"
        ),
        timeout=10000,
    )
    expect(page.get_by_text(f"Process Model: {display_name}")).to_be_visible(
        timeout=10000
    )

    # 5. Update the process model display name
    new_display = f"{display_name} edited"
    edit_btn = page.get_by_test_id("edit-process-model-button")
    expect(edit_btn).to_be_visible(timeout=10000)
    edit_btn.click()

    # Verify navigation to edit form
    expect(page).to_have_url(
        re.compile(
            rf".*/process-models/{re.escape(group_path)}:{re.escape(model_id)}/edit$"
        ),
        timeout=10000,
    )

    edit_input = page.locator('input[name="display_name"]')
    expect(edit_input).to_be_visible()
    edit_input.fill(new_display)
    expect(edit_input).to_have_value(new_display)

    update_btn = page.get_by_role("button", name="Submit")
    expect(update_btn).to_be_enabled()
    update_btn.click()

    # Confirm updated detail page
    expect(page).to_have_url(
        re.compile(
            rf".*/process-models/{re.escape(group_path)}:{re.escape(model_id)}$"
        ),
        timeout=10000,
    )
    expect(page.get_by_text(f"Process Model: {new_display}")).to_be_visible(
        timeout=10000
    )

    # 6. Delete the process model
    delete_btn = page.get_by_test_id("delete-process-model-button")
    expect(delete_btn).to_be_visible(timeout=10000)
    delete_btn.click()

    # Confirm deletion dialog appears
    expect(page.get_by_text("Are you sure")).to_be_visible(timeout=10000)
    # Click the destructive confirm button
    confirm_btn = page.get_by_role("button", name="Delete")
    expect(confirm_btn).to_be_visible(timeout=10000)
    confirm_btn.click()

    # 7. Verify deletion: back to group page, model no longer appears
    expect(page).to_have_url(
        re.compile(rf".*/process-groups/{re.escape(group_path)}$"),
        timeout=10000,
    )
    expect(page.get_by_text(model_id)).to_have_count(0)
    expect(page.get_by_text(new_display)).to_have_count(0)

    # 8. Log out
    logout(page)
