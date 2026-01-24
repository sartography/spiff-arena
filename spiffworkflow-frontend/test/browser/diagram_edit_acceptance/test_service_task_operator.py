import os
import re
from urllib.parse import urlparse, urlunparse

from playwright.sync_api import Page, expect

from diagram_edit_acceptance.helpers import open_diagram, select_element, expand_group_if_needed

SERVICE_TASK_ID = "Activity_1wbmh1r"


def test_service_task_operator_visible(page: Page) -> None:
    open_diagram(page, SERVICE_TASK_ID)
    select_element(page, SERVICE_TASK_ID)

    group = page.locator(
        ".bio-properties-panel-group",
        has_text="Spiffworkflow Service Properties",
    )
    expect(group, "Service properties group visible").to_be_visible(timeout=10000)
    expand_group_if_needed(group)

    expect(group.get_by_text("Operator ID"), "Operator ID label visible").to_be_visible(
        timeout=10000
    )

    operator_value = group.locator("#bio-properties-panel-selectOperatorId")
    expect(operator_value, "Operator ID field visible").to_be_visible(timeout=10000)
    expect(operator_value, "Operator ID field enabled").to_be_enabled(timeout=10000)

    base_url = os.getenv("E2E_URL", "http://localhost:7001")
    parsed = urlparse(base_url)
    port = parsed.port or 80
    api_port = port - 1 if parsed.hostname in ("localhost", "127.0.0.1") else port
    api_base = urlunparse(
        (parsed.scheme, f"{parsed.hostname}:{api_port}", "/v1.0", "", "", "")
    )
    api_url = (
        f"{api_base}/process-models/"
        "system:diagram-edit-acceptance-test:test-a/files/test-a.bpmn"
    )
    cookies = page.context.cookies(api_url)
    access_token = next(
        (cookie["value"] for cookie in cookies if cookie["name"] == "access_token"),
        None,
    )
    auth_id = next(
        (
            cookie["value"]
            for cookie in cookies
            if cookie["name"] == "authentication_identifier"
        ),
        "default",
    )
    assert access_token, "Access token cookie is available"
    response = page.request.get(
        api_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "SpiffWorkflow-Authentication-Identifier": auth_id,
        },
    )
    assert response.ok, "File fetch succeeds after selection"
    payload = response.json()
    file_contents = payload.get("file_contents", "")
    assert re.search(
        r'<spiffworkflow:serviceTaskOperator\\s+id=\"http/GetRequest\"',
        file_contents,
    ), "HTTP GET is selected"
    assert re.search(
        r'<spiffworkflow:parameter\\s+name=\"url\"[^>]*>[^<]+</spiffworkflow:parameter>',
        file_contents,
    ), "URL parameter set"
