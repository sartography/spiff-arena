import pytest

# In order to use the Playwright test runner fixture 'page',
# we must use Playwright's test runner, not plain pytest.
# This file will be rewritten using Playwright's own test runner API via 'pytest-playwright'.
# To use the Playwright fixture, 'pytest-playwright' plugin must be enabled and installed.

from playwright.sync_api import Page, expect
# Assuming helpers are now relative to the tests directory root
from ..helpers.login import login


def start_process(page: Page):
    page.goto("http://localhost:7001/processes")
    page.get_by_role("heading", name="Processes").wait_for(timeout=3000)
    first_row = page.locator('[data-testid="process-row"]').first
    first_row.wait_for(timeout=3000)
    first_row.click()
    run_btn = page.get_by_role("button", name="Run BPMN")
    run_btn.wait_for(timeout=3000)
    run_btn.click()
    page.get_by_role("heading").filter(has_text="Task").wait_for(timeout=5000) # Increased timeout


def submit_form_field(page: Page, task_name: str, field_key: str, field_value: str, check_draft_data: bool = False):
    assert page.get_by_text(f"Task: {task_name}").is_visible(timeout=10000)
    field = page.locator(field_key)
    field.fill("")
    field.type(field_value)
    page.wait_for_timeout(100)
    if check_draft_data:
        page.wait_for_timeout(1000)
        page.reload()
        assert page.locator(field_key).input_value() == field_value
    page.get_by_role("button", name="Submit").click()


def go_home_and_resume(page: Page):
    page.get_by_role("link", name="Home").click()
    page.wait_for_url("http://localhost:7001/")
    resume_btn = page.get_by_role("button", name="Go")
    resume_btn.wait_for(timeout=3000)
    resume_btn.click()


def test_can_complete_and_navigate_a_form(page: Page):
    # Use the imported login helper
    login(page, "admin", "admin")
    start_process(page)
    submit_form_field(
        page, "Step 1", 'input[name="person_name"]', "John Doe", check_draft_data=True
    )
    submit_form_field(
        page, "Step 2", 'input[name="city"]', "Toronto", check_draft_data=True
    )
    go_home_and_resume(page)
    submit_form_field(page, "Step 3", 'input[name="age"]', "30", check_draft_data=True)
    submit_form_field(
        page, "Step 4", 'input[name="favorite_color"]', "Blue", check_draft_data=True
    )
    page.get_by_role("link", name="Home").click()
    page.wait_for_url("http://localhost:7001/")
    status_text = page.locator('[data-testid="workflow-status"]').first.text_content()
    assert status_text is not None
    assert "complete" in status_text.lower()
