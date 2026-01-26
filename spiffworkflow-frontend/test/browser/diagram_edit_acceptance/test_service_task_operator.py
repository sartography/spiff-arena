import re

from playwright.sync_api import Page, expect

from diagram_edit_acceptance.config import CONFIG
from diagram_edit_acceptance.helpers import (
    open_diagram,
    ensure_group_visible,
    expand_group_if_needed,
    locate,
    select_element,
)

SERVICE_TASK_ID = "Activity_1wbmh1r"


def test_service_task_operator_visible(page: Page) -> None:
    open_diagram(page, SERVICE_TASK_ID)
    ensure_group_visible(page, SERVICE_TASK_ID, CONFIG["groups"]["service"])

    group = page.locator(f'[data-group-id="{CONFIG["groups"]["service"]}"]')
    expect(group, "Service properties group visible").to_be_visible(timeout=10000)
    select_element(page, SERVICE_TASK_ID)
    expand_group_if_needed(group)

    operator_select = locate(
        page, CONFIG["selectors"]["service_operator_select"], group
    )
    expect(operator_select, "Operator ID field visible").to_be_visible(timeout=10000)

    expected_operator = "http/GetRequest"
    expect(
        operator_select,
        "Operator ID updated",
    ).to_have_value(expected_operator, timeout=20000)

    params_group = page.locator(
        f'[data-group-id="{CONFIG["groups"]["service_params"]}"]'
    )
    expect(params_group, "Service parameters group visible").to_be_visible(timeout=10000)

    params_group.evaluate(
        """(groupEl) => {
        const toggle = groupEl.querySelector('button[title="Toggle section"]');
        toggle?.click();
        const entry = groupEl.querySelector('.bio-properties-panel-collapsible-entry');
        const entryToggle = entry?.querySelector('button[title="Toggle list item"]');
        entryToggle?.click();
        }"""
    )
    page.wait_for_function(
        """() => {
        const group = document.querySelector('[data-group-id="group-serviceTaskParameters"]');
        const entry = group && group.querySelector('.bio-properties-panel-collapsible-entry');
        const input = entry && entry.querySelector('input, textarea');
        return !!(input && input.value && input.value.includes('spiffdemo.org/api/v1.0/status'));
        }"""
    )
    url_value = page.evaluate(
        """() => {
        const group = document.querySelector('[data-group-id="group-serviceTaskParameters"]');
        const entry = group && group.querySelector('.bio-properties-panel-collapsible-entry');
        const input = entry && entry.querySelector('input, textarea');
        return input ? input.value : null;
        }"""
    )
    assert url_value and "spiffdemo.org/api/v1.0/status" in url_value
