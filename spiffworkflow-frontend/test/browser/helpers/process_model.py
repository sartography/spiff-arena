import re
from playwright.sync_api import Page, expect


def delete_process_model(page: Page, expected_group_path: str):
    """
    Deletes the currently viewed process model through the More Actions menu.

    Args:
        page: Playwright Page object
        expected_group_path: The group path to expect after deletion (for verification)
    """
    # Click the more actions menu button first
    more_actions_btn = page.get_by_test_id("more-actions-button")
    expect(more_actions_btn, "More actions button visible").to_be_visible(timeout=10000)
    more_actions_btn.click()

    # Then click the delete menu item
    delete_menu_item = page.get_by_test_id("delete-process-model-menu-item")
    expect(delete_menu_item, "Delete menu item visible").to_be_visible(timeout=10000)
    delete_menu_item.click()

    # Confirm deletion dialog appears
    expect(page.get_by_text("Are you sure"), "Delete confirmation visible").to_be_visible(timeout=10000)

    # Click the destructive confirm button
    confirm_btn = page.get_by_role("button", name="Delete")
    expect(confirm_btn, "Confirm delete button visible").to_be_visible(timeout=10000)
    confirm_btn.click()

    # Verify deletion: back to group page
    expect(page, "Returned to group page after delete").to_have_url(
        re.compile(rf".*/process-groups/{re.escape(expected_group_path)}$"),
        timeout=10000
    )


def delete_process_model_and_verify_removal(page: Page, expected_group_path: str, model_id: str, display_name: str):
    """
    Deletes the currently viewed process model and verifies it's removed from the listing.

    Args:
        page: Playwright Page object
        expected_group_path: The group path to expect after deletion (for verification)
        model_id: The model ID to verify is removed
        display_name: The display name to verify is removed
    """
    delete_process_model(page, expected_group_path)

    # Verify the model no longer appears in the listing
    expect(page.get_by_text(model_id), "Model id removed").to_have_count(0)
    expect(page.get_by_text(display_name), "Model name removed").to_have_count(0)