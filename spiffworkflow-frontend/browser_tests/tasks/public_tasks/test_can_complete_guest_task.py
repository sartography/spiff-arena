import pytest
from playwright.sync_api import expect, Page, BrowserContext
from helpers.login import login, logout
from helpers.playwright_setup import browser_context
from helpers.debug import print_page_details

# List ALL groups and models for debugging
def list_all_groups_and_models(page):
    print("-- Listing all process groups (tiles/rows) --")
    all_group_tiles = page.locator('[data-testid^="group-list-group-name-"]')
    n = all_group_tiles.count()
    print(f"GROUP TILE COUNT: {n}")
    for i in range(n):
        print(f"GROUP TILE {i}: {all_group_tiles.nth(i).text_content()}")
    group_rows = page.locator('[data-testid^="process-group-row-"]')
    m = group_rows.count()
    print(f"GROUP ROW COUNT: {m}")
    for i in range(m):
        print(f"GROUP ROW {i}: {group_rows.nth(i).text_content()}")
    print("-- END group dump --")

def goto_processes_section(page, base_url):
    nav_div = page.locator('[data-testid="nav-processes"]')
    if nav_div.is_visible():
        nav_div.click()
        page.wait_for_timeout(350)
    # Both sidebar and nav button usually available
    page.goto(f"{base_url}/app/processes")
    page.wait_for_timeout(350)
    expect(page).not_to_have_url("/", timeout=2500)

# Test entrypoint
def test_can_complete_guest_task(browser_context: BrowserContext):
    base_url = "http://localhost:7001"
    group_display_name = "Shared Resources"
    model_display_name = "task-with-guest-form"
    page = browser_context.new_page()
    login(page, "admin", "admin", base_url)

    print("After login:", page.url)
    print_page_details(page)
    goto_processes_section(page, base_url)
    print("After nav to processes:", page.url)
    print_page_details(page)
    list_all_groups_and_models(page)

    # Try group as TILE first
    group_selector = f'[data-testid="group-list-group-name-{group_display_name}"]'
    if page.locator(group_selector).count() > 0 and page.locator(group_selector).is_visible():
        page.locator(group_selector).click()
    else:
        # Try legacy row selector for process groups
        alt = None
        import re
        expected_text = re.sub(r"[^a-zA-Z0-9]", "", group_display_name).lower()
        for i in range(page.locator('[data-testid^="process-group-row-"]').count()):
            row = page.locator('[data-testid^="process-group-row-"]').nth(i)
            txt = row.text_content()
            if txt and expected_text in re.sub(r"[^a-zA-Z0-9]", "", txt).lower():
                alt = row
                break
        if alt:
            print(f"Clicking process group row for: {group_display_name}")
            alt.click()
        else:
            raise Exception(f"Could not find group tile or row for '{group_display_name}'")

    model_selector = f'[data-testid="model-list-model-name-{model_display_name}"]'
    expect(page.locator(model_selector)).to_be_visible(timeout=4000)
    page.locator(model_selector).click()

    run_button = page.locator('[data-testid="run-process"]')
    expect(run_button).to_be_visible(timeout=4000)
    run_button.click()

    confirm_button = page.locator('[data-testid="run-process-confirm"]')
    if not confirm_button.is_visible():
        confirm_button = page.get_by_role("button", name="Start")
    if not confirm_button.is_visible():
        confirm_button = page.get_by_role("button", name="Run")
    expect(confirm_button).to_be_visible()
    confirm_button.click()

    expect(page.locator('[data-testid="process-metadata-section"]')).to_be_visible(timeout=5000)
    link_locator = page.locator('[data-testid="metadata-value-first_task_url"] a')
    expect(link_locator).to_be_visible(timeout=2000)
    href_value = link_locator.get_attribute("href")
    assert href_value, "Could not extract guest task public link!"

    logout(page, base_url)

    guest_page = browser_context.new_page()
    guest_page.goto(href_value)

    submit1 = guest_page.get_by_text("Submit", exact=True)
    expect(submit1).to_be_visible(timeout=2000)
    submit1.click()
    submit2 = guest_page.get_by_text("Submit", exact=True)
    expect(submit2).to_be_visible(timeout=2000)
    submit2.click()
    expect(guest_page.get_by_text("You are done. Yay!", exact=False)).to_be_visible(timeout=3000)
    guest_page.goto(href_value)
    expect(guest_page.get_by_text("Error retrieving content.", exact=False)).to_be_visible(timeout=3000)
    public_home = guest_page.locator('[data-testid="public-home-link"]')
    expect(public_home).to_be_visible(timeout=1000)
    public_home.click()
    public_sign_out = guest_page.locator('[data-testid="public-sign-out"]')
    expect(public_sign_out).to_be_visible(timeout=1000)
    public_sign_out.click()

    found_signin_message = False
    try:
        if guest_page.get_by_text("Sign in to your account").is_visible():
            found_signin_message = True
    except Exception:
        pass
    try:
        if guest_page.locator("#spiff-login-button").is_visible():
            found_signin_message = True
    except Exception:
        pass
    assert found_signin_message, "Did not find login prompt or sign-in message after public sign out."
