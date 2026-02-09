from playwright.sync_api import Page, expect

from diagram_edit_acceptance.helpers import open_diagram, select_element, get_save_button

USER_TASK_ID = "Activity_1v4njcq"


def get_label_text(page: Page) -> str:
    return page.evaluate(
        """(id) => {
        const el = document.querySelector(`g[data-element-id="${id}"] text`);
        return el?.textContent?.trim() || '';
      }""",
        USER_TASK_ID,
    )


def test_can_rename_activity_by_double_clicking_label(page: Page) -> None:
    open_diagram(page, USER_TASK_ID)
    select_element(page, USER_TASK_ID)

    # Wait for the label to have text starting with "user task" before reading it
    import re
    label_element = page.locator(f'g[data-element-id="{USER_TASK_ID}"] text').first
    expect(label_element, "Label should be loaded").to_have_text(
        re.compile(r"^user task"), timeout=10000
    )

    current_label = get_label_text(page)
    new_label = "user task edited" if current_label != "user task edited" else "user task"

    target = page.locator(f'g[data-element-id="{USER_TASK_ID}"]')
    expect(target, "Diagram element visible for editing").to_be_visible(timeout=10000)
    label = target.locator("text").first
    label.dispatch_event("dblclick")

    editor = page.locator('.djs-direct-editing-content')
    expect(editor, "Inline label editor visible").to_be_visible(timeout=10000)

    page.keyboard.press("ControlOrMeta+A")
    page.keyboard.insert_text(new_label)

    page.locator(".canvas").click(position={"x": 10, "y": 10})
    expect(editor, "Inline label editor closed").to_be_hidden(timeout=10000)

    expect(
        page.locator(f'g[data-element-id="{USER_TASK_ID}"] text').first,
        "Label updated in diagram",
    ).to_have_text(new_label, timeout=10000)

    save_button = get_save_button(page)
    expect(save_button, "Save enabled after rename").to_be_enabled(timeout=10000)
    save_button.click()
    expect(save_button, "Save completes after click").to_have_text(
        "Save", timeout=20000
    )

    page.reload()
    reloaded_label = page.locator(f'g[data-element-id="{USER_TASK_ID}"] text').first
    expect(reloaded_label, "Renamed label persists after reload").to_have_text(
        new_label, timeout=20000
    )
