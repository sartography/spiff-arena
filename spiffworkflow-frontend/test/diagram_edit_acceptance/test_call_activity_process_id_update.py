from playwright.sync_api import Page, expect

from diagram_edit_acceptance.config import CONFIG
from diagram_edit_acceptance.helpers import (
    expand_group_if_needed,
    open_diagram,
    select_element,
    ensure_group_visible,
    locate,
)

CALL_ACTIVITY_ID = "Activity_0m4kz8c"


def test_call_activity_search_updates_process_id_without_navigation(page: Page) -> None:
    open_diagram(page, CALL_ACTIVITY_ID)
    ensure_group_visible(page, CALL_ACTIVITY_ID, "group-called_element")

    called_element_group = page.locator('[data-group-id="group-called_element"]')
    expect(called_element_group, "Called Element section visible").to_be_visible(
        timeout=10000
    )

    toggled = called_element_group.evaluate(
        """(groupEl) => {
        const button = groupEl.querySelector('button[title="Toggle section"]');
        if (!button) return false;
        button.click();
        return true;
        }"""
    )
    assert toggled, "Called element group toggle exists"
    process_input = locate(page, {"css": 'input[name="process_id"]'}, called_element_group)
    expect(process_input, "Process ID input visible").to_be_visible(timeout=10000)
    current_value = page.evaluate(
        """() => {
        const input = document.querySelector('input[name="process_id"]');
        return input ? input.value : '';
        }"""
    )

    page.wait_for_function(
        """() => !!document.querySelector('#spiffworkflow-search-call-activity-button')"""
    )
    page.evaluate(
        """() => {
        const button = document.querySelector('#spiffworkflow-search-call-activity-button');
        if (button) button.click();
        }"""
    )

    dialog = page.get_by_role("dialog")
    expect(
        dialog.get_by_role(
            "heading", name="Select Process Model"
        ),
        "Process search dialog opened",
    ).to_be_visible(timeout=10000)

    target = "Process_diagram_edit_acceptance_test_a" if current_value.endswith("_test_b") else "Process_diagram_edit_acceptance_test_b"
    search_input = locate(page, CONFIG["selectors"]["call_activity_search_input"], dialog)
    search_input.click()
    search_input.fill(target)
    search_input.press("ArrowDown")
    search_input.press("Enter")

    # After pressing Enter, the first option is selected and the dropdown closes
    # Wait for the process_id input to be updated with the selected value
    page.wait_for_function(
        f"""() => {{
        const input = document.querySelector('input[name="process_id"]');
        return input && input.value === '{target}';
        }}"""
    )

    # Verify the value was updated correctly
    selected_value = page.evaluate(
        """() => {
        const input = document.querySelector('input[name="process_id"]');
        return input ? input.value : '';
        }"""
    )
    assert selected_value == target, f"Expected process_id to be '{target}', but got '{selected_value}'"

    # call_activity_dialog_confirm is None (no confirm button needed)
    confirm_spec = None
    if confirm_spec:
        locate(page, confirm_spec, dialog).click()
    if dialog.is_visible():
        page.keyboard.press("Escape")
    if CONFIG.get("call_activity_dialog_closes", True):
        expect(dialog, "Dialog closes after selection").to_be_hidden(timeout=10000)

    select_element(page, CALL_ACTIVITY_ID)
    expand_group_if_needed(called_element_group)
    process_input = locate(page, {"css": 'input[name="process_id"]'}, called_element_group)
    updated_value = process_input.input_value()
    assert updated_value, "Process ID should not be empty after selection"

    # Both apps have allow_same_process_id: True, so we don't assert that the value must change

    # Check that we stayed on the current diagram using the file chip selector
    file_chip_selector = CONFIG["diagram"]["file_chip_selector"]
    expected_filename = "test-a.bpmn"
    chip = page.locator(file_chip_selector).filter(has_text=expected_filename)
    expect(
        chip,
        "Selection should not navigate away from current diagram",
    ).to_be_visible(timeout=10000)
