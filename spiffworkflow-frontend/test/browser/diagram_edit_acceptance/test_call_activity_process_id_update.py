from playwright.sync_api import Page, expect

from diagram_edit_acceptance.helpers import (
    expand_group_if_needed,
    open_diagram,
    select_element,
)

CALL_ACTIVITY_ID = "Activity_0m4kz8c"


def test_call_activity_search_updates_process_id_without_navigation(
    page: Page,
) -> None:
    open_diagram(page, CALL_ACTIVITY_ID)
    select_element(page, CALL_ACTIVITY_ID)

    called_element_group = page.locator('[data-group-id="group-called_element"]')
    expect(called_element_group, "Called Element section visible").to_be_visible(
        timeout=10000
    )

    process_input = page.locator('input[name="process_id"]')
    current_value = process_input.input_value()

    search_button = called_element_group.locator('button:has-text("Search")')
    if not search_button.is_visible():
        expand_group_if_needed(called_element_group)
    search_button.click(force=True)

    dialog = page.get_by_role("dialog")
    expect(
        dialog.get_by_role("heading", name="Select Process Model"),
        "Process search dialog opened",
    ).to_be_visible(timeout=10000)

    search_input = dialog.get_by_label("Process model search")
    if not search_input.is_visible():
        search_input = dialog.locator('input[placeholder="Choose a process"]')
    search_input.click()
    search_input.press("ArrowDown")

    options = page.get_by_role("option")
    expect(options.first, "Process options listed").to_be_visible(timeout=10000)

    option_texts = options.all_text_contents()
    target_index = 0
    for idx, text in enumerate(option_texts):
        if current_value and current_value not in text:
            target_index = idx
            break

    options.nth(target_index).click()
    expect(dialog, "Dialog closes after selection").to_be_hidden(timeout=10000)

    updated_value = process_input.input_value()
    assert updated_value, "Process ID should not be empty after selection"
    if current_value:
        assert (
            updated_value != current_value
        ), "Process ID should update after selection"

    expect(
        page.get_by_text("Process Model File: test-a.bpmn"),
        "Selection should not navigate away from current diagram",
    ).to_be_visible(timeout=10000)
