from playwright.sync_api import Page, expect

from diagram_edit_acceptance.helpers import (
    open_diagram,
    select_element,
    expand_group_if_needed,
    open_and_close_dialog,
)

MANUAL_TASK_ID = "Activity_1cb46uw"


def test_can_launch_instructions_editor_from_manual_task(page: Page) -> None:
    open_diagram(page, MANUAL_TASK_ID)
    select_element(page, MANUAL_TASK_ID)

    group = page.locator(
        ".bio-properties-panel-group",
        has_text="Instructions",
    )
    expect(group, "Instructions group visible").to_be_visible(timeout=10000)
    expand_group_if_needed(group)

    launch_button = group.locator('button:has-text("Launch Editor")').first
    launch_button.click(force=True)

    open_and_close_dialog(page, "Edit Markdown")
