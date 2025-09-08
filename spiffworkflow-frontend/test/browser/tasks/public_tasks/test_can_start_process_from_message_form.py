import sys
import os
import pytest
from playwright.sync_api import expect, Page

from helpers.login import login
from helpers.debug import print_page_details


def test_can_start_process_from_message_form(page: Page):
    """Tests starting a process via a public message form."""
    page.goto("http://localhost:7001/public/misc:bounty_start_multiple_forms")

    # 3. Enter first name, submit
    page.fill("#root_firstName", "MyFirstName")
    page.get_by_text("Submit", exact=True).click()

    # 4. Enter last name, submit
    page.fill("#root_lastName", "MyLastName")
    page.get_by_text("Submit", exact=True).click()

    # 5. Confirm the completion message is shown with combined name
    expect(
        page.get_by_text("We hear you. Your name is MyFirstName MyLastName.")
    ).to_be_visible()
