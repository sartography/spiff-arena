import pytest
from playwright.sync_api import Page, expect, BrowserContext
from ..helpers.login import login
from ..helpers.playwright_setup import browser_context
from ..helpers.debug import print_page_details

def start_process(page: Page):
    """Attempt to start a process for workflow test."""
    page.goto("http://localhost:7001/processes")
    page.wait_for_load_state("networkidle")
    process_rows = page.locator('[data-testid="process-row"]')
    process_row_ct = process_rows.count()
    if process_row_ct == 0:
        print_page_details(page)
        raise AssertionError("There are no available processes to test workflow forms.")
    else:
        for idx in range(process_row_ct):
            process_row = process_rows.nth(idx)
            try:
                process_row.click()
                run_btn = page.get_by_role("button", name="Run BPMN")
                expect(run_btn).to_be_visible(timeout=4000)
                run_btn.click()
                break
            except Exception:
                page.go_back()
                continue
        else:
            print_page_details(page)
            raise AssertionError("No process in the list allows for a Run BPMN workflow start.")
    # Wait for something matching a task step
    page.get_by_text("Task:", timeout=10000)

def submit_form_field(page: Page, task_name: str, field_key: str, field_value: str, check_draft_data: bool = False):
    try:
        expect(page.get_by_text(f"Task: {task_name}")).to_be_visible(timeout=10000)
        field = page.locator(field_key)
        expect(field).to_be_visible(timeout=10000)
        field.fill("")
        field.type(field_value)
        if check_draft_data:
            page.wait_for_timeout(1000)
            page.reload()
            expect(field).to_be_visible(timeout=5000)
            expect(field).to_have_value(field_value)
        page.get_by_role("button", name="Submit").click()
    except Exception:
        print_page_details(page)
        raise

def go_home_and_resume(page: Page):
    page.get_by_role("link", name="Home").click()
    page.wait_for_url("http://localhost:7001/")
    resume_btn = page.get_by_role("button", name="Go")
    expect(resume_btn).to_be_visible(timeout=8000)
    resume_btn.click()


def test_can_complete_and_navigate_a_form(browser_context: BrowserContext):
    """Tests completing a multi-step form, including navigating away and back."""
    page = browser_context.new_page()
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
    try:
        expect(page.locator('[data-testid="workflow-status"]').first).to_contain_text(
            "complete", ignore_case=True, timeout=8000
        )
    except Exception:
        print_page_details(page)
        raise
