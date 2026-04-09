import re

from playwright.sync_api import Page, expect

from diagram_edit_acceptance.helpers import (
    open_diagram,
    open_message_editor,
    select_element,
)

MESSAGE_START_EVENT_ID = "StartEvent_1"


def test_can_open_message_editor_from_start_event(page: Page) -> None:
    open_diagram(page, MESSAGE_START_EVENT_ID)
    select_element(page, MESSAGE_START_EVENT_ID)

    dialog = open_message_editor(page)
    assert dialog is None
    expect(page).to_have_url(
        re.compile(
            r"/messages\?message_id=start-message-diagram-edit-acceptance-test"
            r"&source_location=system%2Fdiagram-edit-acceptance-test%2Ftest-a$"
        )
    )
    expect(
        page.get_by_role("dialog").get_by_role(
            "heading",
            name=(
                "start-message-diagram-edit-acceptance-test "
                "(system/diagram-edit-acceptance-test)"
            ),
        )
    ).to_be_visible(timeout=10000)
