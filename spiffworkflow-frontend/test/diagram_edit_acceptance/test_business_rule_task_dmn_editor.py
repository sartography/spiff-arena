from playwright.sync_api import Page, expect

from diagram_edit_acceptance.config import CONFIG
from diagram_edit_acceptance.helpers import (
    open_diagram,
    select_element,
    expand_group_if_needed,
    locate,
)

BUSINESS_RULE_TASK_ID = "Activity_04orcix"


def test_can_launch_dmn_editor_from_business_rule_task(page: Page) -> None:
    open_diagram(page, BUSINESS_RULE_TASK_ID)
    select_element(page, BUSINESS_RULE_TASK_ID)

    group = page.locator('[data-group-id="group-business_rule_properties"]')
    expect(group, "Business rule properties group visible").to_be_visible(timeout=10000)
    expand_group_if_needed(group)

    launch_button = locate(page, {"css": "#launch_editor_button_spiffworkflow\\:CalledDecisionId"}, group)
    expect(launch_button, "Launch Editor button visible").to_be_visible(timeout=10000)
    launch_button.click()

    # Verify we navigated to the DMN file
    file_chip_selector = CONFIG["diagram"]["file_chip_selector"]
    expected_filename = "simple.dmn"
    chip = page.locator(file_chip_selector).filter(has_text=expected_filename)
    expect(
        chip,
        "Navigated to DMN editor",
    ).to_be_visible(timeout=20000)

    # Verify DMN content is visible (the decision table name)
    expect(
        page.get_by_text("simple_decision"),
        "DMN decision table rendered",
    ).to_be_visible(timeout=20000)
