import pytest
from playwright.sync_api import expect, Page, BrowserContext
from helpers.login import login, logout, BASE_URL
from helpers.debug import print_page_details
from helpers.playwright_setup import browser_context

PROCESS_GROUP = "Shared Resources"
PROCESS_MODEL = "task-with-guest-form"


def start_process_and_get_public_link(page: Page) -> str:
    # 1. Login and navigate to process group
    login(page, "admin", "admin", base_url=BASE_URL)
    page.goto(f"{BASE_URL}/process-groups")
    # Select the Shared Resources group
    page.get_by_text(PROCESS_GROUP, exact=False).first.click()
    # Ensure group page loaded
    expect(page.get_by_test_id(f"process-group-breadcrumb-{PROCESS_GROUP}"))
    # 2. Select the target process model
    page.get_by_test_id(f"process-model-card-{PROCESS_MODEL}").first.click()
    # Ensure model detail page
    expect(page.get_by_text(f"Process Model: {PROCESS_MODEL}"))
    # 3. Start the process
    start_button = page.get_by_test_id("start-process-instance").first
    expect(start_button).to_be_visible()
    start_button.click(no_wait_after=True)
    # Wait for interstitial metadata page
    page.wait_for_url("**/interstitial", timeout=15000)
    # DEBUG: print page details to inspect metadata fields
    print_page_details(page)
    # DEBUG: print full page content
    print("PAGE CONTENT START")
    print(page.content())
    print("PAGE CONTENT END")
    pytest.skip("Debugging interstitial page content")
    # 4. Extract the public guest task URL
    metadata_link = page.locator('[data-testid="metadata-value-first_task_url"] a')
    expect(metadata_link).to_be_visible()
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


def test_can_complete_guest_task(browser_context: BrowserContext):
    page = browser_context.new_page()
    # Start process and get link
    public_task_url = start_process_and_get_public_link(page)
    # Logout as admin
    logout(page, base_url=BASE_URL)
    # Complete the guest task forms as unauthenticated user
    complete_guest_task_flow(page, public_task_url)
    # Verify link cannot be reused
    page.goto(public_task_url)
    expect(page.get_by_text("Error retrieving content.")).to_be_visible()
    # Navigate to public home and sign out
    home_link = page.get_by_test_id("public-home-link")
    expect(home_link).to_be_visible()
    home_link.click()
    sign_out = page.get_by_test_id("public-sign-out")
    expect(sign_out).to_be_visible()
    sign_out.click()
    # After sign out, verify login page or sign-in prompt
    login_button = page.locator("#spiff-login-button")
    sign_in_prompt = page.get_by_text("Sign in to your account", exact=False)
    if login_button.is_visible():
        expect(login_button).to_be_visible()
    else:
        expect(sign_in_prompt).to_be_visible()
