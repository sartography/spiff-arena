import re

from playwright.sync_api import Page, expect

from diagram_edit_acceptance.config import CONFIG
from diagram_edit_acceptance.helpers import (
    open_diagram,
    ensure_group_visible,
    expand_group_if_needed,
    expand_entry_if_needed,
    locate,
    select_element,
)

SERVICE_TASK_ID = "Activity_1wbmh1r"


def test_service_task_operator_visible(page: Page) -> None:
    open_diagram(page, SERVICE_TASK_ID)
    ensure_group_visible(page, SERVICE_TASK_ID, "group-service_task_properties")

    group = page.locator('[data-group-id="group-service_task_properties"]')
    expect(group, "Service properties group visible").to_be_visible(timeout=10000)
    select_element(page, SERVICE_TASK_ID)
    expand_group_if_needed(group)
    expect(
        page.locator('input[name="id"]'),
        "Service task selected",
    ).to_have_value(SERVICE_TASK_ID, timeout=10000)

    operator_select = locate(group, CONFIG["selectors"]["service_operator_select"])
    expect(operator_select, "Operator ID field visible").to_be_visible(timeout=10000)

    params_group = page.locator('[data-group-id="group-serviceTaskParameters"]')
    expect(params_group, "Service parameters group visible").to_be_visible(timeout=10000)
    expand_group_if_needed(params_group)

    entry = params_group.locator(".bio-properties-panel-collapsible-entry").first
    expand_entry_if_needed(entry)

    url_input = entry.locator("input, textarea").first
    expect(
        url_input,
        "Service parameters URL populated",
    ).to_have_value(re.compile(r"spiffdemo\.org/api/v1\.0/status"), timeout=20000)
