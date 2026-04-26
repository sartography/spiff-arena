from playwright.sync_api import Page, expect

from diagram_edit_acceptance.config import CONFIG
from diagram_edit_acceptance.helpers import (
    open_diagram,
    select_element,
    expand_group_if_needed,
    open_and_close_dialog,
    locate,
)

MANUAL_TASK_ID = "Activity_1cb46uw"


def test_can_launch_instructions_editor_from_manual_task(page: Page) -> None:
    open_diagram(page, MANUAL_TASK_ID)
    select_element(page, MANUAL_TASK_ID)

    group = page.locator('[data-group-id="group-instructions"]')
    expect(group, "Instructions group visible").to_be_visible(timeout=10000)
    expand_group_if_needed(group)

    launch_button = locate(page, CONFIG["selectors"]["instructions_open"], group)
    launch_button.click(force=True)

    open_and_close_dialog(page, CONFIG["dialog_headings"]["instructions"])
