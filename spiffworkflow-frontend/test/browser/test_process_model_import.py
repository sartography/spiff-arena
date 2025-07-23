import uuid
import re
from playwright.sync_api import expect, BrowserContext

from helpers.login import login, logout, BASE_URL
from helpers.playwright_setup import browser_context  # fixture


def test_process_model_import(browser_context: BrowserContext):
    """Test importing a process model from GitHub."""
    page = browser_context.new_page()

    # 1. Login as admin
    login(page, "admin", "admin")

    # 2. Create a new process group to import into
    unique = uuid.uuid4().hex
    group_id = f"test-import-group-{unique}"
    group_name = f"Test Import Group {unique}"

    page.goto(f"{BASE_URL}/process-groups/new")
    expect(page).to_have_url(re.compile(r"/process-groups/new$"), timeout=10000)

    # Fill in the process group form
    page.get_by_label("Display Name").fill(group_name)
    page.get_by_label("ID").fill(group_id)

    # Submit the form
    page.get_by_role("button", name="Submit").click()

    # Verify we are on the new group's page
    expect(page).to_have_url(re.compile(fr"/process-groups/{group_id}$"), timeout=10000)

    # 3. Go to create a new process model in this group to get to the import button
    page.goto(f"{BASE_URL}/process-models/{group_id}/new")

    # The import button should be visible on this page
    import_button = page.get_by_test_id("process-model-import-button").first
    expect(import_button).to_be_visible(timeout=10000)
    import_button.click()

    # 4. Fill out and submit the import dialog
    dialog = page.get_by_role("dialog")
    expect(dialog).to_be_visible(timeout=10000)

    # Find the input field and enter the GitHub URL
    input_field = dialog.locator("input[placeholder*='github.com']").first
    expect(input_field).to_be_visible(timeout=10000)
    input_field.fill(
        "https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example"
    )

    # Click the import button in the dialog
    dialog_import_button = dialog.get_by_test_id("import-button").first
    expect(dialog_import_button).to_be_visible(timeout=10000)
    expect(dialog_import_button).to_be_enabled(timeout=10000)
    dialog_import_button.click()

    # 5. Verify the import was successful
    # After successful import, we're redirected to the imported model page
    expect(page).to_have_url(re.compile(fr"/process-models/{group_id}:0-1-minimal-example"), timeout=15000)

    # Verify the imported model page content
    # We're on the model page, but let's just verify the URL is correct
    # We'll skip checking for specific elements on the page as they may change
    
    # 6. Clean up: first navigate back to the process group page
    page.goto(f"{BASE_URL}/process-groups/{group_id}")
    expect(page).to_have_url(re.compile(fr"/process-groups/{group_id}$"), timeout=10000)
    delete_btn = page.get_by_test_id("delete-process-group-button")
    expect(delete_btn).to_be_visible(timeout=10000)
    delete_btn.click()

    # Confirm deletion dialog appears
    expect(page.get_by_text("Are you sure")).to_be_visible(timeout=10000)
    # Click the destructive confirm button
    confirm_btn = page.get_by_role("button", name="Delete")
    expect(confirm_btn).to_be_visible(timeout=10000)
    confirm_btn.click()

    # Verify deletion: back to group list page
    expect(page).to_have_url(re.compile(r"/process-groups$"), timeout=10000)
    
    # Wait for any deletion process to complete
    page.wait_for_timeout(2000)  # Wait 2 seconds
    
    # Refresh the page to ensure we get the latest state
    page.reload()
    
    # Verify the group is no longer listed
    page.wait_for_timeout(1000)  # Wait 1 more second after reload
    expect(page.get_by_text(group_name)).to_have_count(0, timeout=5000)

    # 7. Log out
    logout(page)
