import re

from playwright.sync_api import Page, expect

from diagram_edit_acceptance.config import CONFIG
from diagram_edit_acceptance.helpers import (
    open_diagram,
    ensure_group_visible,
    open_script_editor,
    read_script_text,
    set_script_text,
    close_script_editor,
    get_save_button,
)

SCRIPT_TASK_ID = "Activity_0qpzdpu"


def test_can_edit_script_task_using_launch_editor(page: Page) -> None:
    open_diagram(page, SCRIPT_TASK_ID)
    ensure_group_visible(page, SCRIPT_TASK_ID, "group-spiff_script")

    dialog = open_script_editor(page)
    updated_script = "a = 2"

    set_script_text(page, dialog, updated_script)
    close_script_editor(page, dialog, "apply_button")

    save_button = get_save_button(page)
    expect(save_button, "Save enabled after script change").to_be_enabled(timeout=10000)
    save_button.click()

    ensure_group_visible(page, SCRIPT_TASK_ID, "group-spiff_script")
    dialog = open_script_editor(page)
    updated_text = ""
    for _ in range(3):
        updated_text = read_script_text(dialog)
        if re.search(r"^a\s*=\s*2$", updated_text.strip(), re.M):
            break
        page.wait_for_timeout(300)
    assert re.search(r"^a\s*=\s*2$", updated_text.strip(), re.M), (
        "Script update persisted in editor after reopen"
    )
    close_script_editor(page, dialog, "close_button")
