import pytest
from playwright.sync_api import expect, Page, BrowserContext
from helpers.login import login, logout
from helpers.debug import print_page_details
from helpers.playwright_setup import browser_context
import time

PROCESS_GROUP = "Shared Resources"
PROCESS_MODEL = "task-with-guest-form"
BASE_URL = "http://localhost:7001"
ADMIN_USER = "admin"
ADMIN_PASS = "admin"

# Try: go to /process_models/[group:model], then look for a start button there.
def start_process_and_get_public_link(page: Page) -> str:
    login(page, ADMIN_USER, ADMIN_PASS, base_url=BASE_URL)
    page.goto(f"{BASE_URL}/process_models/misc:task-with-guest-form")
    print_page_details(page)
    # Look for start button(s)
    found = False
    # First, try data-testid run-model-primary
    run_btn = page.get_by_test_id("run-model-primary")
    if run_btn.is_visible():
        run_btn.click()
        for _ in range(10):
            metadata_locator = page.locator('[data-testid="metadata-value-first_task_url"] a')
            if metadata_locator.is_visible():
                public_task_url = metadata_locator.get_attribute("href")
                if public_task_url:
                    return public_task_url
            time.sleep(0.5)
    # Fallback: try all Start This Process visible buttons
    start_buttons = page.locator('button:has-text("Start this process")')
    for idx in range(start_buttons.count()):
        btn = start_buttons.nth(idx)
        if btn.is_visible():
            btn.click()
            for _ in range(10):
                metadata_locator = page.locator('[data-testid="metadata-value-first_task_url"] a')
                if metadata_locator.is_visible():
                    public_task_url = metadata_locator.get_attribute("href")
                    if public_task_url:
                        return public_task_url
                time.sleep(0.5)
    print_page_details(page)
    raise AssertionError("No public (guest) task URL found after run attempts (even on model detail page).")

def complete_guest_task_flow(page: Page, task_url: str):
    page.goto(task_url)
    for _ in range(2):
        submit_button = page.get_by_text("Submit", exact=True)
        expect(submit_button).to_be_visible()
        submit_button.click()
    expect(page.get_by_text("You are done. Yay!", exact=False)).to_be_visible()

def test_can_complete_guest_task(browser_context: BrowserContext):
    page = browser_context.new_page()
    public_task_url = start_process_and_get_public_link(page)
    logout(page, base_url=BASE_URL)
    complete_guest_task_flow(page, public_task_url)
    page.goto(public_task_url)
    expect(page.get_by_text("Error retrieving content.")).to_be_visible()
    home_link = page.get_by_test_id("public-home-link")
    expect(home_link).to_be_visible()
    home_link.click()
    sign_out = page.get_by_test_id("public-sign-out")
    expect(sign_out).to_be_visible()
    sign_out.click()
    login_button = page.locator("#spiff-login-button")
    sign_in_prompt = page.get_by_text("Sign in to your account", exact=False)
    if login_button.is_visible():
        expect(login_button).to_be_visible()
    else:
        expect(sign_in_prompt).to_be_visible()
