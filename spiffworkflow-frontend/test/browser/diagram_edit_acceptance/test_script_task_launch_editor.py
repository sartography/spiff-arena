import re

from playwright.sync_api import Page, expect

from helpers.url import get_base_url

BASE_URL = get_base_url()
MODEL_FILE_URL = (
    f"{BASE_URL}/process-models/"
    "system:diagram-edit-acceptance-test:test-a/files/test-a.bpmn"
)
SCRIPT_TASK_ID = "Activity_0qpzdpu"


def open_diagram(page: Page) -> None:
    page.goto(MODEL_FILE_URL)
    expect(page.get_by_text("Process Model File: test-a.bpmn"), "Diagram loaded").to_be_visible(
        timeout=20000
    )
    page.get_by_role("button", name="Fit to View").click()
    expect(
        page.locator(f'g[data-element-id="{SCRIPT_TASK_ID}"]'),
        "Script task rendered",
    ).to_be_visible(timeout=20000)


def select_element(page: Page, element_id: str) -> None:
    target = page.locator(f'g[data-element-id="{element_id}"]')
    hit = page.locator(f'g[data-element-id="{element_id}"] .djs-hit')
    for _ in range(3):
        page.evaluate(
            """(id) => {
            const el = document.querySelector(`g[data-element-id="${id}"]`);
            if (el) el.scrollIntoView({ block: 'center', inline: 'center' });
          }""",
            element_id,
        )
        if hit.count() > 0:
            hit.first.click(force=True)
        else:
            target.click(force=True)
        if page.locator('input[name="id"]').input_value() == element_id:
            return
        page.wait_for_timeout(250)
        page.evaluate(
            """(id) => {
            const el = document.querySelector(`g[data-element-id="${id}"]`);
            if (!el) return false;
            ['mousedown','mouseup','click'].forEach((type) =>
              el.dispatchEvent(new MouseEvent(type, { bubbles: true }))
            );
            return true;
          }""",
            element_id,
        )
        if page.locator('input[name="id"]').input_value() == element_id:
            return
        page.wait_for_timeout(250)
    expect(
        page.locator('input[name="id"]'),
        "Properties panel updated for selected element",
    ).to_have_value(element_id, timeout=10000)


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
    return dialog.locator(".view-lines").inner_text().strip()


def set_editor_text(page: Page, dialog, text: str) -> None:
    editor = dialog.locator(".monaco-editor")
    editor.click()
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")
    page.keyboard.type(text)


def test_can_edit_script_task_using_launch_editor(page: Page) -> None:
    open_diagram(page)
    select_element(page, SCRIPT_TASK_ID)

    dialog = open_script_editor(page)
    current_script = read_editor_text(dialog)
    updated_script = "a = 2" if "a = 1" in current_script else "a = 1"

    set_editor_text(page, dialog, updated_script)
    dialog.get_by_role("button", name=re.compile(r"close", re.I)).click()

    save_button = page.get_by_test_id("process-model-file-save-button")
    expect(save_button, "Save enabled after script change").to_be_enabled(timeout=10000)
    save_button.click()
    expect(save_button, "Save completes after click").to_be_disabled(timeout=20000)

    select_element(page, SCRIPT_TASK_ID)
    dialog = open_script_editor(page)
    updated_text = read_editor_text(dialog)
    expect(updated_text, "Script update persisted").to_contain(updated_script)
    dialog.get_by_role("button", name=re.compile(r"close", re.I)).click()
