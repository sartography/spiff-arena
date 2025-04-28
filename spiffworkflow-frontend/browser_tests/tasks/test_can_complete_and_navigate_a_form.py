import re
import pytest
from playwright.sync_api import expect, Page, BrowserContext

from helpers.login import login, logout, BASE_URL
from helpers.debug import print_page_details
from helpers.playwright_setup import browser_context  # fixture


def submit_input_into_form_field(
    page: Page,
    task_name: str,
    field_selector: str,
    field_value: str,
    check_draft: bool = False,
):
    # Wait for task name to appear
    page.get_by_text(f"Task: {task_name}").wait_for(timeout=10000)
    # Fill and submit
    page.locator(field_selector).fill(str(field_value))
    # debounce
    page.wait_for_timeout(100)
    if check_draft:
        page.wait_for_timeout(1000)
        page.reload()
        expect(page.locator(field_selector)).to_have_value(str(field_value))
    page.get_by_text("Submit").click()


def test_can_complete_and_navigate_a_form(browser_context: BrowserContext):
    page = browser_context.new_page()
    # 1. Log in
    login(page, "admin", "admin")

    parent_group = "Shared Resources"
    child_group = "Acceptance Tests Group One"
    model_display_name = "Acceptance Tests Model 2"
    completed_task_class = "completed-task-highlight"
    active_task_class = "active-task-highlight"

    # 2. Navigate to process-groups listing
    page.goto(f"{BASE_URL}/process-groups")

    # 3. Select parent group
    page.get_by_text(parent_group, exact=False).first.click()
    expect(
        page.locator(f'[data-testid="process-group-breadcrumb-{parent_group}"]')
    ).to_be_visible()

    # 4. Select child group
    page.get_by_text(child_group, exact=False).first.click()
    # DEBUG: after clicking child group
    print_page_details(page)
    expect(
        page.locator(f'[data-testid="process-group-breadcrumb-{child_group}"]')
    ).to_be_visible()

    # 5. Select process model
    page.locator(
        f'[data-testid="process-model-card-{model_display_name}"]',
        has_text=model_display_name,
    ).click()
    expect(page.get_by_text(f"Process Model: {model_display_name}")).to_be_visible()

    # 6. Start the process instance
    page.get_by_test_id("start-process-instance").click()

    # 7. Complete form 1
    submit_input_into_form_field(
        page, "get_form_num_one", "#root_form_num_1", 2, check_draft=True
    )

    # 8. Complete form 2
    submit_input_into_form_field(page, "get_form_num_two", "#root_form_num_2", 3)

    # 9. Complete form 3
    submit_input_into_form_field(page, "get_form_num_three", "#root_form_num_3", 4)

    # 10. Navigate to process instance list
    page.get_by_test_id("process-instance-list-link").click()
    rows = page.locator("tbody tr")
    assert rows.count() >= 1

    # 11. Open first instance
    page.get_by_test_id("process-instance-show-link-id").first.click()
    expect(page.get_by_text("Process Instance Id:", exact=False)).to_be_visible()

    # 12. Inspect form3 details
    page.locator('g[data-element-id="form3"]').click()
    expect(page.get_by_text('"form_num_1": 2')).to_be_visible()
    expect(page.get_by_text('"form_num_2": 3')).to_be_visible()
    expect(page.get_by_text('"form_num_3": 4')).to_be_visible()
    assert page.get_by_text('"form_num_4": 5').count() == 0
    expect(page.locator('g[data-element-id="form1"]').first).to_have_class(
        completed_task_class
    )
    expect(page.locator('g[data-element-id="form2"]').first).to_have_class(
        completed_task_class
    )
    expect(page.locator('g[data-element-id="form3"]').first).to_have_class(
        completed_task_class
    )
    expect(page.locator('g[data-element-id="form4"]').first).to_have_class(
        active_task_class
    )

    # 13. Close details modal
    page.locator(".is-visible .cds--modal-close").click()

    # 14. Go to Home and resume
    page.get_by_test_id("header-menu-expand-button").click()
    page.get_by_test_id("side-nav-items").get_by_text("Home").click()
    expect(page.get_by_text("Waiting for me")).to_be_visible()
    page.get_by_text("Go", exact=True).click()

    # 15. Complete form 4
    submit_input_into_form_field(page, "get_form_num_four", "#root_form_num_4", 5)
    assert "/tasks" in page.url

    # 16. Verify final completion status
    page.goto(f"{BASE_URL}/process-groups")
    page.get_by_text(parent_group, exact=False).first.click()
    page.get_by_text(child_group, exact=False).first.click()
    page.locator(
        '[data-testid="process-model-show-link"]', has_text=model_display_name
    ).click()
    page.get_by_test_id("process-instance-list-link").click()
    page.get_by_test_id("process-instance-show-link-id").first.click()
    expect(
        page.locator(".process-instance-status").get_by_text("complete")
    ).to_be_visible()

    # 17. Logout
    logout(page)
