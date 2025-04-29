import uuid
from playwright.sync_api import BrowserContext

from helpers.login import login, BASE_URL
from helpers.playwright_setup import browser_context
from helpers.debug import print_page_details

def test_process_group_form_debug(browser_context: BrowserContext):
    page = browser_context.new_page()
    login(page, "admin", "admin")
    page.goto(f"{BASE_URL}/process-groups/new")
    print_page_details(page)
    assert False, "Debug form"
