import os
import pytest
from playwright.sync_api import sync_playwright

# Configure headless mode via environment variable HEADLESS (default: true)
HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"


@pytest.fixture(scope="function")
def browser_context(request):
    """
    Provides a Playwright browser context for tests.
    Handles browser launch and cleanup.
    """
    with sync_playwright() as p:
        # You might want to parameterize the browser type (chromium, firefox, webkit)
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context()
        # Optional: Pass command line args to the fixture if needed
        # e.g., context.set_default_timeout(request.config.getoption("--timeout"))
        yield context
        # Teardown: Close the browser after the test function finishes
        browser.close()
