import pytest
from playwright.sync_api import sync_playwright, expect


def base_url():
    return "http://localhost:7001"


def test_login_and_navigate():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Navigate to the initial URL.
        page.goto(f"{base_url()}/newui")

        # Wait for the username field to appear (assuming redirect to login).
        page.wait_for_selector("#username")

        page.fill("#username", "nelson")
        page.fill("#password", "nelson")
        page.click("#spiff-login-button")

        # Wait for navigation to complete after login.  We'll wait for the
        # target element to appear as a proxy for successful login and redirect.
        page.wait_for_selector('[data-qa="nav-start-new process"]')

        # Click the "Start New Process" navigation element.
        page.click('[data-qa="nav-start-new process"]')

        # Add an assertion here - for example, check the URL after clicking.
        # Replace '/expected_url' with the actual URL you expect.
        expect(page).to_have_url("http://localhost:7001/newui/startprocess")

        # get screenshot
        page.goto(f"{base_url()}/newui/process-models/site-administration:heyo")
        locator = page.locator("h1")
        expect(locator).to_have_text("Process Model: heyo")
        page.screenshot(path="new.png")

        page.goto(f"{base_url()}/process-models/site-administration:heyo")
        locator = page.locator("h1")
        expect(locator).to_have_text("Process Model: heyo")
        page.screenshot(path="old.png")

        browser.close()


if __name__ == "__main__":
    pytest.main([__file__])
