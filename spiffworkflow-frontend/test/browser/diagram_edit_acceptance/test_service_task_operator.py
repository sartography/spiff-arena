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
    header_toggle = group.locator(".bio-properties-panel-group-header button")
    if not group.get_by_text("Operator ID").is_visible():
        if header_toggle.count() > 0:
            header_toggle.first.click()
        else:
            expand_group_if_needed(group)

    expect(group.get_by_text("Operator ID"), "Operator ID label visible").to_be_visible(
        timeout=10000
    )

    operator_value = group.get_by_role("combobox", name="Operator ID")
    expect(operator_value, "Operator ID field visible").to_be_visible(timeout=10000)
    expect(operator_value, "Operator ID field enabled").to_be_enabled(timeout=10000)
    operator_value.click()
    page.wait_for_function(
        """() => {
        const select = document.querySelector('#bio-properties-panel-selectOperatorId');
        return select && select.options && select.options.length > 0;
        }""",
        timeout=20000,
    )
    expect(operator_value, "HTTP GET is selected").to_have_value(
        "http/GetRequest", timeout=20000
    )

    page.evaluate(
        """() => {
        const group = Array.from(document.querySelectorAll('.bio-properties-panel-group'))
          .find((g) => g.textContent?.includes('Spiffworkflow Service Properties'));
        if (!group) return false;
        const paramsToggle = Array.from(group.querySelectorAll('button[title=\"Toggle section\"]'))
          .find((btn) => btn.parentElement?.textContent?.includes('Parameters'));
        paramsToggle?.click();
        const urlHeader = Array.from(
          group.querySelectorAll('.bio-properties-panel-collapsible-entry-header-title'),
        ).find((el) => el.textContent === 'url');
        const urlButton = urlHeader?.parentElement?.querySelector(
          "button[title='Toggle list item']",
        );
        urlButton?.click();
        return !!urlButton;
        }"""
    )
    page.wait_for_function(
        """() => {
        return Array.from(document.querySelectorAll('input, textarea')).some(
          (el) => el.value && el.value.includes('spiffdemo.org/api/v1.0/status'),
        );
        }""",
        timeout=10000,
    )
