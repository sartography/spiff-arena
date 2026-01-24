import re

from playwright.sync_api import Page, expect

from diagram_edit_acceptance.helpers import MODEL_FILE_URL, open_diagram, select_element, expand_group_if_needed
CALL_ACTIVITY_ID = "Activity_0m4kz8c"




def test_can_search_and_select_process_for_call_activity(page: Page) -> None:
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
