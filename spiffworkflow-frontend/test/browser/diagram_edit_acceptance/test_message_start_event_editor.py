from playwright.sync_api import Page, expect

from diagram_edit_acceptance.helpers import (
    open_diagram,
    select_element,
    expand_group_if_needed,
    open_and_close_dialog,
)

MESSAGE_START_EVENT_ID = "StartEvent_1"


def test_can_open_message_editor_from_start_event(page: Page) -> None:
    open_diagram(page, MESSAGE_START_EVENT_ID)
    select_element(page, MESSAGE_START_EVENT_ID)

    group = page.locator(
        ".bio-properties-panel-group",
        has_text="Message",
    )
    expect(group, "Message group visible").to_be_visible(timeout=10000)
    expand_group_if_needed(group)

    open_button = group.locator('button:has-text("Open message editor")').first
    expect(open_button, "Open message editor button visible").to_be_visible(
        timeout=10000
    )
    open_button.click(force=True)

    open_and_close_dialog(page, "Message Editor")
