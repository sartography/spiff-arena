import uuid
from playwright.sync_api import Page

def print_page_details(page: Page):
    try:
        print(f"\n[DEBUG] Page Title: {page.title()}")
        print(f"[DEBUG] Page URL: {page.url}")
        screenshot_path = f"/tmp/screenshot_{uuid.uuid4()}.png"
        page.screenshot(path=screenshot_path)
        print(f"[DEBUG] Screenshot saved to {screenshot_path}")
        print(f"[DEBUG] Page Content:\n{page.content()}\n")
    except Exception as e:
        print(f"\n[DEBUG] Error getting page details: {e}")