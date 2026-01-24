import re

from playwright.sync_api import Page, expect

from helpers.url import get_base_url

BASE_URL = get_base_url()
MODEL_FILE_URL = (
    f"{BASE_URL}/process-models/"
    "system:diagram-edit-acceptance-test:test-a/files/test-a.bpmn"
)
CALL_ACTIVITY_ID = "Activity_0m4kz8c"


def open_diagram(page: Page) -> None:
    page.goto(MODEL_FILE_URL)
    expect(page.get_by_text("Process Model File: test-a.bpmn"), "Diagram loaded").to_be_visible(
        timeout=20000
    )
    expect(
        page.locator(f'g[data-element-id="{CALL_ACTIVITY_ID}"]'),
        "Call activity rendered",
    ).to_be_visible(timeout=20000)


def select_element(page: Page, element_id: str) -> None:
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
    target = page.locator(f'g[data-element-id="{element_id}"]')
    hit = page.locator(f'g[data-element-id="{element_id}"] .djs-hit')
    target.scroll_into_view_if_needed()
    if hit.count() > 0:
        hit.first.click(force=True)
    else:
        target.click(force=True)
    expect(
        page.locator('input[name="id"]'),
        "Properties panel updated for selected element",
    ).to_have_value(element_id, timeout=10000)


def test_can_search_and_select_process_for_call_activity(page: Page) -> None:
    open_diagram(page)
    select_element(page, CALL_ACTIVITY_ID)

    called_element_group = page.locator('[data-group-id="group-called_element"]')
    expect(called_element_group, "Called Element section visible").to_be_visible(
        timeout=10000
    )

    process_input = page.locator('input[name="process_id"]')
    current_value = process_input.input_value()

    search_button = called_element_group.locator('button:has-text("Search")')
    if not search_button.is_visible():
        called_element_group.locator('.bio-properties-panel-group-header-title').click(
            force=True
        )
    search_button.click(force=True)

    dialog = page.get_by_role("dialog")
    expect(
        dialog.get_by_role("heading", name=re.compile(r"Select Process Model", re.I)),
        "Process search dialog opened",
    ).to_be_visible(timeout=10000)

    search_input = dialog.get_by_label("Process model search")
    if not search_input.is_visible():
        search_input = dialog.locator('input[placeholder="Choose a process"]')
    search_input.click()
    search_input.press("ArrowDown")

    options = page.get_by_role("option")
    expect(options.first, "Process options listed").to_be_visible(timeout=10000)

    option_text = options.first.inner_text().strip()
    options.first.click()

    expect(dialog, "Dialog closes after selection").to_be_hidden(timeout=10000)

    updated_value = process_input.input_value()
    match = re.search(r"\(([^)]+)\)\s*$", option_text)
    if match:
        expect(process_input, "Process ID updated").to_have_value(match.group(1))
    else:
        assert updated_value, "Process ID should not be empty after selection"
