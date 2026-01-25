from playwright.sync_api import Page, expect

from diagram_edit_acceptance.config import CONFIG
from diagram_edit_acceptance.helpers import (
    open_diagram,
    select_element,
    expand_group_if_needed,
    open_and_close_dialog,
    locate,
)

USER_TASK_ID = "Activity_1v4njcq"


def test_can_launch_json_schema_editor_from_user_task(page: Page) -> None:
    open_diagram(page, USER_TASK_ID)
    select_element(page, USER_TASK_ID)

    group = page.locator(f'[data-group-id="{CONFIG["groups"]["user_task"]}"]')
    expect(group, "Web form group visible").to_be_visible(timeout=10000)
    expand_group_if_needed(group)

    launch_button = locate(page, CONFIG["selectors"]["script_launch"], group)
    launch_button.click(force=True)

    open_and_close_dialog(page, CONFIG["dialog_headings"]["json_schema"])
