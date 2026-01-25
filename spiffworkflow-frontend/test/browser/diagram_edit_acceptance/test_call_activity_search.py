from playwright.sync_api import Page, expect

from diagram_edit_acceptance.helpers import open_diagram, select_element, expand_group_if_needed
CALL_ACTIVITY_ID = "Activity_0m4kz8c"




def test_can_search_and_select_process_for_call_activity(page: Page) -> None:
    open_diagram(page, CALL_ACTIVITY_ID)
    select_element(page, CALL_ACTIVITY_ID)

    called_element_group = page.locator('[data-group-id="group-called_element"]')
    expect(called_element_group, "Called Element section visible").to_be_visible(
        timeout=10000
    )

    launch_button = called_element_group.locator(
        'button:has-text("Launch Editor")'
    )
    if not launch_button.is_visible():
        expand_group_if_needed(called_element_group)
    launch_button.click(force=True)

    expect(
        page.get_by_text("Process Model File: test-b.bpmn"),
        "Navigated to called process model",
    ).to_be_visible(timeout=20000)
    expect(
        page.get_by_text("script task b"),
        "Called process diagram rendered",
    ).to_be_visible(timeout=20000)
