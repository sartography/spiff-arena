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
    # Wait for task header to ensure form is loaded
    page.get_by_text(f"Task: {task_name}", exact=True).wait_for(timeout=10000)
    # Wait for field to be present
    page.wait_for_selector(field_selector, timeout=10000)
    # Locate all matching inputs and pick the first visible and enabled
    locator = page.locator(field_selector)
    visible_input = None
    for i in range(locator.count()):
        inp = locator.nth(i)
        try:
            if inp.is_visible() and inp.is_enabled():
                visible_input = inp
                break
        except Exception:
            continue
    if not visible_input:
        print_page_details(page)
        raise Exception(f"No visible and enabled input found for {field_selector}")
    # Fill the value
    visible_input.fill(str(field_value))
    # Wait for debounce/autosave
    page.wait_for_timeout(200)
    if check_draft:
        page.wait_for_timeout(1000)
        page.reload()
        page.wait_for_selector(field_selector, timeout=10000)
        locator = page.locator(field_selector)
        draft_ok = False
        for i in range(locator.count()):
            inp = locator.nth(i)
            try:
                if inp.is_visible() and inp.is_enabled():
                    expect(inp).to_have_value(str(field_value))
                    draft_ok = True
                    break
            except Exception:
                continue
        if not draft_ok:
            print_page_details(page)
            raise Exception(f"Draft value not found for {field_selector}")
    # Click the Submit button
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

    # 2. Go to process groups listing
    page.goto(f"{BASE_URL}/process-groups")

    # 3. Select parent group
    page.get_by_text(parent_group, exact=False).first.click()
    expect(page.get_by_test_id(f"process-group-breadcrumb-{parent_group}")).to_be_visible()

    # 4. Select child group
    page.get_by_text(child_group, exact=False).first.click()
    expect(page.get_by_test_id(f"process-group-breadcrumb-{child_group}")).to_be_visible()

    # 5. Open process model details
    page.get_by_test_id(f"process-model-card-{model_display_name}").first.click()
    expect(page.get_by_text(f"Process Model: {model_display_name}", exact=False)).to_be_visible()

    # 6. Start the process instance
    page.get_by_test_id("start-process-instance").first.click()

    # 7. Complete form 1 with draft check
    submit_input_into_form_field(page, "get_form_num_one", "#root_form_num_1", 2, check_draft=True)

    # 8. Complete form 2
    submit_input_into_form_field(page, "get_form_num_two", "#root_form_num_2", 3)

    # 9. Complete form 3
    submit_input_into_form_field(page, "get_form_num_three", "#root_form_num_3", 4)

    # 10. Ensure form 4 is next
    page.get_by_text("Task: get_form_num_four", exact=True).wait_for(timeout=10000)

    # 11. Navigate to process instance list via model page
    page.goto(f"{BASE_URL}/process-groups")
    page.get_by_text(parent_group, exact=False).first.click()
    expect(page.get_by_test_id(f"process-group-breadcrumb-{parent_group}")).to_be_visible()
    page.get_by_text(child_group, exact=False).first.click()
    expect(page.get_by_test_id(f"process-group-breadcrumb-{child_group}")).to_be_visible()
    page.get_by_test_id(f"process-model-card-{model_display_name}").first.click()
    expect(page.get_by_text(f"Process Model: {model_display_name}", exact=False)).to_be_visible()
    page.get_by_test_id("process-instance-list-link").click()
    rows = page.locator("tbody tr")
    assert rows.count() >= 1

    # 12. Open first instance details
    page.get_by_test_id("process-instance-show-link-id").first.click()
    expect(page.get_by_text("Process Instance Id:", exact=False)).to_be_visible()

    # 13. Inspect form3 details and status highlighting
    page.locator('g[data-element-id="form3"]').click()
    expect(page.get_by_text('"form_num_1": 2')).to_be_visible()
    expect(page.get_by_text('"form_num_2": 3')).to_be_visible()
    expect(page.get_by_text('"form_num_3": 4')).to_be_visible()
    assert page.get_by_text('"form_num_4": 5').count() == 0
    expect(page.locator('g[data-element-id="form1"]').first).to_have_class(completed_task_class)
    expect(page.locator('g[data-element-id="form2"]').first).to_have_class(completed_task_class)
    expect(page.locator('g[data-element-id="form3"]').first).to_have_class(completed_task_class)
    expect(page.locator('g[data-element-id="form4"]').first).to_have_class(active_task_class)

    # 14. Close the details modal
    page.locator('.is-visible .cds--modal-close').click()

    # 15. Navigate to Home and resume
    page.get_by_test_id("header-menu-expand-button").click()
    page.get_by_test_id("side-nav-items").get_by_text("Home").click()
    expect(page.get_by_text("Waiting for me", exact=False)).to_be_visible()
    page.get_by_text("Go", exact=True).click()

    # 16. Complete form 4
    submit_input_into_form_field(page, "get_form_num_four", "#root_form_num_4", 5)
    assert "/tasks" in page.url

    # 17. Verify final completion status on instance show
    page.goto(f"{BASE_URL}/process-groups")
    page.get_by_text(parent_group, exact=False).first.click()
    page.get_by_text(child_group, exact=False).first.click()
    page.get_by_test_id(f"process-model-card-{model_display_name}").first.click()
    expect(page.get_by_text(f"Process Model: {model_display_name}", exact=False)).to_be_visible()
    page.get_by_test_id("process-instance-list-link").click()
    page.get_by_test_id("process-instance-show-link-id").first.click()
    expect(page.locator(".process-instance-status").get_by_text("complete")).to_be_visible()

    # 18. Logout
    logout(page)
