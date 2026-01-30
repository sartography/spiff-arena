from playwright.sync_api import Page, expect

from diagram_edit_acceptance.config import CONFIG
from diagram_edit_acceptance.helpers import (
    open_diagram,
    select_element,
    open_and_close_dialog,
)

USER_TASK_ID = "Activity_1v4njcq"


def test_can_launch_json_schema_editor_from_user_task(page: Page) -> None:
    open_diagram(page, USER_TASK_ID)
    select_element(page, USER_TASK_ID)

    group = page.locator('[data-group-id="group-user_task_properties"]')
    expect(group, "Web form group visible").to_be_visible(timeout=10000)
    toggled = group.evaluate(
        """(groupEl) => {
        const button = groupEl.querySelector('button[title="Toggle section"]');
        if (!button) return false;
        button.click();
        return true;
        }"""
    )
    assert toggled, "Web form group toggle exists"

    page.wait_for_function(
        """() => !!document.querySelector('#launch_editor_button_formJsonSchemaFilename')"""
    )
    page.evaluate(
        """() => {
        const button = document.querySelector('#launch_editor_button_formJsonSchemaFilename');
        if (button) button.click();
        }"""
    )

    open_and_close_dialog(page, CONFIG["dialog_headings"]["json_schema"])
