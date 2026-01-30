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
    ensure_group_visible(page, CALL_ACTIVITY_ID, CONFIG["groups"]["call_activity"])

    called_element_group = page.locator(
        f'[data-group-id="{CONFIG["groups"]["call_activity"]}"]'
    )
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
    process_input = locate(
        page, CONFIG["selectors"]["call_activity_process_input"], called_element_group
    )
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
            "heading", name=CONFIG["dialog_headings"]["call_activity"]
        ),
        "Process search dialog opened",
    ).to_be_visible(timeout=10000)

    target = "test-a" if current_value.endswith("_test_b") else "test-b"
    search_input = locate(page, CONFIG["selectors"]["call_activity_search_input"], dialog)
    search_input.click()
    search_input.fill(target)
    search_input.press("ArrowDown")
    search_input.press("Enter")

    options = dialog.get_by_role("option")
    if options.count() > 0:
        option_texts = options.all_text_contents()
        target_index = 0
        for idx, text in enumerate(option_texts):
            if current_value and current_value not in text:
                target_index = idx
                break

        # Ensure we select a different option when allow_same_process_id is False
        allow_same = CONFIG.get("call_activity", {}).get("allow_same_process_id", False)
        if not allow_same and options.count() > 1:
            if current_value and current_value in option_texts[target_index]:
                # Try to find first option that doesn't contain current_value
                found_different = False
                for idx, text in enumerate(option_texts):
                    if current_value not in text:
                        target_index = idx
                        found_different = True
                        break
                # If all options contain current_value, pick a different index
                if not found_different and target_index == 0:
                    target_index = 1

        options.nth(target_index).click()

    confirm_spec = CONFIG["selectors"].get("call_activity_dialog_confirm")
    if confirm_spec:
        locate(page, confirm_spec, dialog).click()
    if dialog.is_visible():
        page.keyboard.press("Escape")
    if CONFIG.get("call_activity_dialog_closes", True):
        expect(dialog, "Dialog closes after selection").to_be_hidden(timeout=10000)

    select_element(page, CALL_ACTIVITY_ID)
    expand_group_if_needed(called_element_group)
    process_input = locate(page, CONFIG["selectors"]["call_activity_process_input"], called_element_group)
    updated_value = process_input.input_value()
    assert updated_value, "Process ID should not be empty after selection"

    allow_same = CONFIG.get("call_activity", {}).get("allow_same_process_id", False)
    if not allow_same:
        assert updated_value != current_value, "Process ID should update after selection"

    # Check that we stayed on the current diagram using the file chip selector
    file_chip_selector = CONFIG["diagram"]["file_chip_selector"]
    expected_filename = "test-a.bpmn"
    chip = page.locator(file_chip_selector).filter(has_text=expected_filename)
    expect(
        chip,
        "Selection should not navigate away from current diagram",
    ).to_be_visible(timeout=10000)
