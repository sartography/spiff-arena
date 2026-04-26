from playwright.sync_api import Page, expect

from diagram_edit_acceptance.config import CONFIG
from diagram_edit_acceptance.helpers import (
    open_diagram,
    locate,
    ensure_group_visible,
)

CALL_ACTIVITY_ID = "Activity_0m4kz8c"


def test_can_search_and_select_process_for_call_activity(page: Page) -> None:
    open_diagram(page, CALL_ACTIVITY_ID)
    ensure_group_visible(page, CALL_ACTIVITY_ID, "group-called_element")

    called_element_group = page.locator('[data-group-id="group-called_element"]')
    expect(called_element_group, "Called Element section visible").to_be_visible(
        timeout=10000
    )

    page.wait_for_function(
        """() => !!document.querySelector('[data-group-id="group-called_element"]')"""
    )
    toggled = page.evaluate(
        """() => {
        const groupEl = document.querySelector('[data-group-id="group-called_element"]');
        if (!groupEl) return false;
        const button = groupEl.querySelector('button[title="Toggle section"]');
        if (!button) return false;
        button.click();
        return true;
        }"""
    )
    assert toggled, "Called element group toggle exists"
    page.wait_for_function(
        """() => !!document.querySelector('#spiffworkflow-open-call-activity-button')"""
    )
    page.evaluate(
        """() => {
        const button = document.querySelector('#spiffworkflow-open-call-activity-button');
        if (button) button.click();
        }"""
    )

    dialog = page.locator('[role="dialog"]')
    page.wait_for_timeout(300)
    if dialog.is_visible():
        expect(
            dialog.get_by_role(
                "heading", name="Select Process Model"
            ),
            "Process selection dialog opened",
        ).to_be_visible(timeout=10000)

        search_input = locate(page, CONFIG["selectors"]["call_activity_search_input"], dialog)
        search_input.click()
        search_input.fill("test-b")
        search_input.press("ArrowDown")
        search_input.press("Enter")
        # call_activity_dialog_confirm is None (no confirm button needed)
        confirm_spec = None
        if confirm_spec:
            locate(page, confirm_spec, dialog).click()

    # Check that we navigated to the called process model using the file chip selector
    file_chip_selector = CONFIG["diagram"]["file_chip_selector"]
    expected_filename = "test-b.bpmn"
    chip = page.locator(file_chip_selector).filter(has_text=expected_filename)
    expect(
        chip,
        "Navigated to called process model",
    ).to_be_visible(timeout=20000)
    expect(
        page.get_by_text("script task b"),
        "Called process diagram rendered",
    ).to_be_visible(timeout=20000)
