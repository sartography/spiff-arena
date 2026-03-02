from playwright.sync_api import expect, Page
from helpers.login import login, logout, BASE_URL
from helpers.debug import print_page_details

PROCESS_GROUP = "Shared Resources"
PROCESS_MODEL = "task-with-guest-form"


def start_process_and_get_public_link(page: Page) -> str:
    # 1. Login and navigate to process group
    login(page, base_url=BASE_URL)
    page.goto(f"{BASE_URL}/process-groups")
    page.get_by_text(PROCESS_GROUP, exact=False).first.click()
    expect(page.get_by_test_id(f"process-group-breadcrumb-{PROCESS_GROUP}"))

    # 2. Select the target process model
    page.get_by_test_id(f"process-model-card-{PROCESS_MODEL}").first.click()
    expect(page.get_by_text(f"Process Model: {PROCESS_MODEL}"))

    # 3. Start the process
    start_button = page.get_by_test_id("start-process-instance").first
    expect(start_button).to_be_visible()
    start_button.click()
    page.wait_for_timeout(1000)

    # 4. Click on "My process instances" tab
    my_instances_tab = page.get_by_text("My process instances", exact=True)
    expect(my_instances_tab).to_be_visible(timeout=10000)
    my_instances_tab.click()

    # 5. Navigate to the newest process instance from the table
    process_instance_link = page.locator(
        '[data-testid="process-instance-show-link-id"]'
    ).first
    expect(process_instance_link).to_be_visible(timeout=10000)
    process_instance_link.click()
    page.wait_for_url("**/process-instances/**", timeout=15000)

    # 6. Extract the public guest task URL from metadata
    metadata_link = page.locator('[data-testid="metadata-value-first_task_url"] a')
    expect(metadata_link).to_be_visible(timeout=10000)
    public_task_url = metadata_link.get_attribute("href")
    if not public_task_url:
        print_page_details(page)
        raise AssertionError("Guest task URL link missing or empty in metadata page.")
    return public_task_url


def complete_guest_task_flow(page: Page, task_url: str):
    # Visit guest task link and complete forms
    page.goto(task_url)
    # There are two sequential forms, each with a Submit button
    for _ in range(2):
        submit_btn = page.get_by_text("Submit", exact=True)
        expect(submit_btn).to_be_visible()
        submit_btn.click()
    # Confirm completion message
    expect(page.get_by_text("You are done. Yay!", exact=False)).to_be_visible()


def test_can_complete_guest_task(page: Page):
    public_task_url = start_process_and_get_public_link(page)
    logout(page, base_url=BASE_URL)
    complete_guest_task_flow(page, public_task_url)

    # Verify link cannot be reused
    page.goto(public_task_url)
    expect(page.get_by_text("Error retrieving content")).to_be_visible()
