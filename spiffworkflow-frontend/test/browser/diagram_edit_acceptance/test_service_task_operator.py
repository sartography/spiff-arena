from playwright.sync_api import Page, expect

from diagram_edit_acceptance.helpers import open_diagram, select_element, expand_group_if_needed

SERVICE_TASK_ID = "Activity_1wbmh1r"


def test_service_task_operator_visible(page: Page) -> None:
    open_diagram(page, SERVICE_TASK_ID)
    select_element(page, SERVICE_TASK_ID)

    group = page.locator(
        ".bio-properties-panel-group",
        has_text="Spiffworkflow Service Properties",
    )
    expect(group, "Service properties group visible").to_be_visible(timeout=10000)
    expand_group_if_needed(group)

    expect(group.get_by_text("Operator ID"), "Operator ID label visible").to_be_visible(
        timeout=10000
    )

    operator_value = group.locator("#bio-properties-panel-selectOperatorId")
    expect(operator_value, "Operator ID field visible").to_be_visible(timeout=10000)
    expect(operator_value, "Operator ID field enabled").to_be_enabled(timeout=10000)
    expect(group.get_by_text("Parameters"), "Parameters section visible").to_be_visible(
        timeout=10000
    )
