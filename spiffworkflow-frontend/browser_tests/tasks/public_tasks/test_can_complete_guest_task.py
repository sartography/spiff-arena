import sys
import os
import pytest
from playwright.sync_api import sync_playwright, expect

helpers_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../helpers"))
if helpers_path not in sys.path:
    sys.path.insert(0, helpers_path)
from login import login, logout
from debug import print_page_details

BASE_URL = "http://localhost:7001"


def test_can_complete_guest_task():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(f"{BASE_URL}/sign-in")
        login(page, "admin", "admin", base_url=BASE_URL)

        # Go to Processes page
        try:
            page.click('[data-testid="nav-processes"]', timeout=7000)
        except Exception:
            print_page_details(page)
            raise
        page.wait_for_load_state('networkidle')
        print("--- After navigating to Processes ---")
        print_page_details(page)

        # Click the group button labeled 'Shared Resources' (just click all and pause for detail)
        group_found = False
        all_buttons = page.get_by_role("button")
        for i in range(all_buttons.count()):
            btn = all_buttons.nth(i)
            text = (btn.text_content() or "").strip()
            if text.startswith("Shared Resources"):
                btn.click()
                group_found = True
                page.wait_for_load_state('networkidle')
                print("--- After clicking Shared Resources group ---")
                print_page_details(page)
                # Click again in case of collapsible tree
                break
        assert group_found, "Could not find/click Shared Resources group!"

        # Look for all 'Start this process' buttons, pick one whose parent div/tr has 'task-with-guest-form'
        found = False
        start_btns = page.locator('button', has_text='Start this process')
        for i in range(start_btns.count()):
            btn = start_btns.nth(i)
            parent = btn.evaluate_handle('el => el.closest("tr") || el.closest("div")')
            parent_text = parent.text_content() if parent else ""
            if "task-with-guest-form" in parent_text:
                btn.click()
                found = True
                break
        if not found:
            print("--- Could not find Start button with task-with-guest-form label ---")
            print_page_details(page)
            raise AssertionError("Could not find a Start this process button for 'task-with-guest-form'!")
        page.wait_for_load_state('networkidle')
        print("--- After process start, checking for metadata link ---")
        print_page_details(page)
        # Try Details or other tab if needed
        details_tab = page.get_by_role("tab", name="Details")
        if details_tab.count() and details_tab.first.is_visible():
            details_tab.first.click()
            page.wait_for_load_state('networkidle')
            print("--- After Details tab ---")
            print_page_details(page)
        # Look for data-testid anywhere on page (not just a)
        meta_locator = page.locator('[data-testid="metadata-value-first_task_url"]')
        meta_locator.wait_for(state="attached", timeout=20000)
        public_task_url = meta_locator.locator('a').get_attribute('href')
        assert public_task_url, "Guest task public link not found!"
        if public_task_url.startswith("/public/"):
            public_task_url = BASE_URL + public_task_url

        # Log out
        logout(page, base_url=BASE_URL)
        
        # Open the public (guest) task URL in a new tab
        guest_page = context.new_page()
        guest_page.goto(public_task_url)
        guest_page.get_by_text("Submit", exact=True).click()
        guest_page.get_by_text("Submit", exact=True).click()
        expect(guest_page.get_by_text("You are done. Yay!")).to_be_visible(timeout=7000)

        # Try to visit the public link again (should error out)
        guest_page.goto(public_task_url)
        expect(guest_page.get_by_text("Error retrieving content.")).to_be_visible(timeout=7000)

        # Click Home and sign out from public side
        guest_page.locator('[data-testid="public-home-link"]').click()
        guest_page.locator('[data-testid="public-sign-out"]').click()
        found_login_text = False
        try:
            expect(guest_page.get_by_text("Sign in to your account")).to_be_visible(timeout=6000)
            found_login_text = True
        except Exception:
            pass
        if not found_login_text:
            expect(guest_page.locator("#spiff-login-button")).to_be_visible(timeout=6000)
        browser.close()
