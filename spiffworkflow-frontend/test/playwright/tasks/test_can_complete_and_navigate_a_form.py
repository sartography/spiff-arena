import re
from playwright.sync_api import expect, Page, BrowserContext

from helpers.login import login, logout, BASE_URL
from helpers.playwright_setup import browser_context  # fixture
from helpers.debug import print_page_details


def submit_input_into_form_field(
    page: Page,
    task_name: str,
    field_selector: str,
    field_value: str,
    check_draft: bool = False,
):
    # Wait for the task header to ensure form is loaded
    page.get_by_text(f"Task: {task_name}", exact=True).wait_for(timeout=10000)
    # Locate input(s) matching selector
    locator = page.locator(field_selector)
    locator.first.wait_for(timeout=10000)
    # Fill the first visible input
    for i in range(locator.count()):
        inp = locator.nth(i)
        if inp.is_visible():
            inp.fill(str(field_value))
            break
    # Wait for autosave
    page.wait_for_timeout(200)
    if check_draft:
        # Allow autosave to persist
        page.wait_for_timeout(1000)
        page.reload()
        # Verify the value is retained
        locator = page.locator(field_selector)
        locator.first.wait_for(timeout=10000)
        for i in range(locator.count()):
            inp = locator.nth(i)
            if inp.is_visible():
                expect(inp).to_have_value(str(field_value))
                break
    # Submit form
    submit_btn = page.get_by_role("button", name="Submit")
    submit_btn.wait_for(state="visible", timeout=10000)
    submit_btn.click()


def test_can_complete_and_navigate_a_form(browser_context: BrowserContext):
    page = browser_context.new_page()
    # 1. Log in
    login(page, "admin", "admin")

    parent_group = "Shared Resources"
    child_group = "Acceptance Tests Group One"
    model_display_name = "Acceptance Tests Model 2"
    completed_task_class = "completed-task-highlight"
    active_task_class = "active-task-highlight"

    # 2-5. Navigate to the process model and start instance
    page.goto(f"{BASE_URL}/process-groups")
    page.get_by_text(parent_group, exact=False).first.click()
    expect(page.get_by_test_id(f"process-group-breadcrumb-{parent_group}")).to_be_visible()
    page.get_by_text(child_group, exact=False).first.click()
    expect(page.get_by_test_id(f"process-group-breadcrumb-{child_group}")).to_be_visible()
    page.get_by_test_id(f"process-model-card-{model_display_name}").first.click()
    expect(page.get_by_text(f"Process Model: {model_display_name}", exact=False)).to_be_visible()
    page.get_by_test_id("start-process-instance").first.click()

    # 6-8. Complete forms 1 through 3
    submit_input_into_form_field(page, "get_form_num_one", "#root_form_num_1", 2, check_draft=True)
    submit_input_into_form_field(page, "get_form_num_two", "#root_form_num_2", 3)
    submit_input_into_form_field(page, "get_form_num_three", "#root_form_num_3", 4)

    # 9. Mid-progress: inspect instance via all instances list
    page.goto(f"{BASE_URL}/process-instances/all")
    expect(page.get_by_text("All Process Instances", exact=False)).to_be_visible()
    instances = page.get_by_test_id("process-instance-show-link-id")
    expect(instances.first).to_be_visible()
    instances.first.click()

    # Verify form3 data and highlighting
    heading = page.get_by_role("heading", name=re.compile(r"Process Instance Id:"))
    heading.wait_for(timeout=10000)
    page.locator('g[data-element-id="form3"]').click()
    expect(page.get_by_text('"form_num_1": 2')).to_be_visible()
    expect(page.get_by_text('"form_num_2": 3')).to_be_visible()
    expect(page.get_by_text('"form_num_3": 4')).to_be_visible()
    assert page.get_by_text('"form_num_4": 5').count() == 0
    # Check highlighting classes via regex
    form1 = page.locator('g[data-element-id="form1"]').first
    form2 = page.locator('g[data-element-id="form2"]').first
    form3 = page.locator('g[data-element-id="form3"]').first
    form4 = page.locator('g[data-element-id="form4"]').first
    expect(form1).to_have_class(re.compile(rf"(^|\s){completed_task_class}($|\s)"))
    expect(form2).to_have_class(re.compile(rf"(^|\s){completed_task_class}($|\s)"))
    expect(form3).to_have_class(re.compile(rf"(^|\s){completed_task_class}($|\s)"))
    expect(form4).to_have_class(re.compile(rf"(^|\s){active_task_class}($|\s)"))
    # Close modal
    page.locator('.is-visible .cds--modal-close').click()

    # 10. Resume form 4 from home
    page.get_by_test_id("nav-home").click()
    expect(page.get_by_text("Waiting for me", exact=False)).to_be_visible()
    page.get_by_text("Go", exact=True).click()

    # 11. Complete form 4
    submit_input_into_form_field(page, "get_form_num_four", "#root_form_num_4", 5)
    expect(page).to_have_url(lambda url: "/tasks" in url)

    # 12. Final: verify instance status is complete
    page.goto(f"{BASE_URL}/process-instances/all")
    instances = page.get_by_test_id("process-instance-show-link-id")
    expect(instances.first).to_be_visible()
    instances.first.click()
    expect(page.locator(".process-instance-status").get_by_text("complete")).to_be_visible()

    # 13. Logout
    logout(page)
