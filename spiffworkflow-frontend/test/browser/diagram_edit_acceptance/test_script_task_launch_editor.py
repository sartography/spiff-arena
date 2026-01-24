import re

from playwright.sync_api import Page, expect

from diagram_edit_acceptance.helpers import MODEL_FILE_URL, open_diagram, select_element
SCRIPT_TASK_ID = "Activity_0qpzdpu"




def open_script_editor(page: Page):
    script_group = page.locator('[data-group-id="group-spiff_script"]')
    expect(script_group, "Script properties visible").to_be_visible(timeout=10000)
    launch_button = script_group.locator('button:has-text("Launch Editor")')
    if not launch_button.is_visible():
        script_group.get_by_text("Script", exact=True).first.click(force=True)
    launch_button.click(force=True)
    dialog = page.get_by_role("dialog")
    expect(
        dialog.get_by_role("heading", name=re.compile(r"Editing Script", re.I)),
        "Script editor dialog opened",
    ).to_be_visible(timeout=10000)
    dialog.locator(".monaco-editor").wait_for(state="visible", timeout=10000)
    return dialog


def read_editor_text(dialog) -> str:
    text = dialog.locator(".view-lines").inner_text().strip()
    return text.replace("\u00a0", " ")


def set_editor_text(page: Page, dialog, text: str) -> None:
    editor = dialog.locator(".monaco-editor")
    editor.click()
    page.keyboard.press("Meta+A")
    page.keyboard.press("Backspace")
    page.keyboard.insert_text(text)


def test_can_edit_script_task_using_launch_editor(page: Page) -> None:
    open_diagram(page, SCRIPT_TASK_ID)
    select_element(page, SCRIPT_TASK_ID)

    dialog = open_script_editor(page)
    updated_script = "a = 2"

    set_editor_text(page, dialog, updated_script)
    dialog.get_by_role("button", name=re.compile(r"close", re.I)).click()

    save_button = page.get_by_test_id("process-model-file-save-button")
    expect(save_button, "Save enabled after script change").to_be_enabled(timeout=10000)
    save_button.click()
    expect(save_button, "Save completes after click").to_be_disabled(timeout=20000)

    select_element(page, SCRIPT_TASK_ID)
    dialog = open_script_editor(page)
    updated_text = ""
    for _ in range(3):
        updated_text = read_editor_text(dialog)
        if re.search(r"^a\s*=\s*2$", updated_text.strip(), re.M):
            break
        page.wait_for_timeout(300)
    assert re.search(r"^a\s*=\s*2$", updated_text.strip(), re.M), (
        "Script update persisted in editor after reopen"
    )
    dialog.get_by_role("button", name=re.compile(r"close", re.I)).click()
