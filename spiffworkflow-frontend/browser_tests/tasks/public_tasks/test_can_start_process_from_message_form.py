import pytest
from playwright.sync_api import Page, expect
# Assuming helpers are now relative to the tests directory root
from ..helpers.login import login, logout

@pytest.mark.parametrize("first, last", [("MyFirstName", "MyLastName")])
def test_can_start_process_from_message_form(page: Page, first, last):
    # Log in and out to reset any authentication state
    login(page, "admin", "admin")
    logout(page)

    # 2. Navigate to public bounty form
    page.goto("http://localhost:7001/public/misc:bounty_start_multiple_forms")
    
    # 3. Enter first name and submit
    page.locator("#root_firstName").fill(first)
    page.get_by_role("button", name="Submit").click()

    # 4. Enter last name and submit
    page.locator("#root_lastName").fill(last)
    page.get_by_role("button", name="Submit").click()

    # 5. Confirm completion message
    expect(page.get_by_text(f"We hear you. Your name is {first} {last}.")).to_be_visible()
