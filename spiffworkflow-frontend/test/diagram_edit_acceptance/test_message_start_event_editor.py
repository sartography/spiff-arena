from playwright.sync_api import Page, expect

from diagram_edit_acceptance.config import CONFIG
from diagram_edit_acceptance.helpers import (
    open_diagram,
    select_element,
    open_and_close_dialog,
    open_message_editor,
)

MESSAGE_START_EVENT_ID = "StartEvent_1"


def test_can_open_message_editor_from_start_event(page: Page) -> None:
    open_diagram(page, MESSAGE_START_EVENT_ID)
    select_element(page, MESSAGE_START_EVENT_ID)

    dialog = open_message_editor(page)
    if dialog:
        open_and_close_dialog(page, "Message Editor")
