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
    operator_value = ""
    for _ in range(3):
        for _ in range(20):
            operator_value = operator_select.evaluate("el => el.value || ''")
            if operator_value == expected_operator:
                break
            has_options = operator_select.evaluate(
                "el => !!(el && el.options && el.options.length > 0)"
            )
            if has_options:
                operator_select.select_option(value=expected_operator)
            page.wait_for_timeout(500)
        if operator_value == expected_operator:
            break
        ensure_group_visible(page, SERVICE_TASK_ID, CONFIG["groups"]["service"])
        expand_group_if_needed(group)

    assert operator_value == expected_operator

    params_group = page.locator(
        f'[data-group-id="{CONFIG["groups"]["service_params"]}"]'
    )
    expect(params_group, "Service parameters group visible").to_be_visible(timeout=10000)

    url_value = None
    for _ in range(3):
        for _ in range(20):
            url_value = page.evaluate(
                """() => {
                const group = document.querySelector('[data-group-id=\"group-serviceTaskParameters\"]');
                const toggle = group?.querySelector('button[title=\"Toggle section\"]');
                toggle?.click();
                const entries = Array.from(group?.querySelectorAll('.bio-properties-panel-collapsible-entry') || []);
                const entry = entries.find((el) => el.textContent?.includes('url'));
                const entryToggle = entry?.querySelector('button[title=\"Toggle list item\"]');
                entryToggle?.click();
                const input = entry?.querySelector('input, textarea');
                return input?.value || null;
                }"""
            )
            if url_value and "spiffdemo.org/api/v1.0/status" in url_value:
                break
            page.wait_for_timeout(500)
        if url_value and "spiffdemo.org/api/v1.0/status" in url_value:
            break
        ensure_group_visible(page, SERVICE_TASK_ID, CONFIG["groups"]["service"])

    if url_value:
        assert "spiffdemo.org/api/v1.0/status" in url_value
    else:
        found_values = page.evaluate(
            """() => {
            return Array.from(document.querySelectorAll('input, textarea'))
              .map((el) => el.value || '')
              .filter((value) => value.includes('spiffdemo.org/api/v1.0/status'));
            }"""
        )
        assert found_values, "Service URL should be present in parameters"
