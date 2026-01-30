import os

BASE_URL = os.getenv("E2E_URL", "http://localhost:7001")

CONFIG = {
    "base_url": BASE_URL,
    "diagram": {
        "url": (
            f"{BASE_URL}/process-models/"
            "system:diagram-edit-acceptance-test:test-a/files/test-a.bpmn"
        ),
        "loaded_text": "test-a.bpmn",
        "file_label_template": "Process Model File: {file}",
        "file_chip_selector": '[data-testid="diagram-file-chip"]',
        "fit_button": {"role": "button", "name": "Fit to View"},
    },
    "login": {
        "url": BASE_URL,
        "username": {"css": "#username"},
        "password": {"css": "#password"},
        "submit": {"css": "#spiff-login-button"},
        "post_login": {"role": "button", "name": "User Actions"},
        "username_env": "BROWSER_TEST_USERNAME",
        "password_env": "BROWSER_TEST_PASSWORD",
        "username_default": "nelson",
        "password_default": "nelson",
    },
    "save_button": {
        "test_id": "process-model-file-save-button",
    },
    "selectors": {
        "call_activity_open": {"role": "button", "name": "Launch Editor"},
        "call_activity_search": {"role": "button", "name": "Search"},
        "call_activity_search_input": {"css": "input"},
        "message_open": {"role": "button", "name": "Open message editor"},
        "instructions_open": {"role": "button", "name": "Launch Editor"},
        "service_operator_select": {"role": "combobox", "name": "Operator ID"},
    },
    "dialog_headings": {
        "script": "Editing Script",
        "instructions": "Edit Markdown",
        "json_schema": "Edit JSON Schema",
    },
    "script_editor": {
        "mode": "monaco",
        "apply_button": "close",
        "close_button": "close",
    },
    "message_editor": {"opens": True},
    "call_activity_dialog_closes": False,
}
