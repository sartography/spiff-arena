import os

BASE_URL = os.getenv("E2E_URL", "http://localhost:7001")

CONFIG = {
    "base_url": BASE_URL,
    "diagram": {
        "url": (
            f"{BASE_URL}/process-models/"
            "system:diagram-edit-acceptance-test:test-a/files/test-a.bpmn"
        ),
        "loaded_text": "Process Model File: test-a.bpmn",
        "file_label_template": "Process Model File: {file}",
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
        "role_name": "Save",
    },
    "groups": {
        "script": "group-spiff_script",
        "instructions": "group-instructions",
        "call_activity": "group-called_element",
        "service": "group-service_task_properties",
        "service_params": "group-serviceTaskParameters",
        "user_task": "group-user_task_properties",
        "message": "group-messages",
    },
    "selectors": {
        "call_activity_open": {"role": "button", "name": "Launch Editor"},
        "call_activity_search": {"role": "button", "name": "Search"},
        "call_activity_search_input": {"css": "input"},
        "call_activity_dialog_confirm": None,
        "message_open": {"role": "button", "name": "Open message editor"},
        "instructions_open": {"role": "button", "name": "Launch Editor"},
        "script_launch": {"role": "button", "name": "Launch Editor"},
        "service_operator_select": {"role": "combobox", "name": "Operator ID"},
        "call_activity_process_input": "input[name=\"process_id\"]",
    },
    "dialog_headings": {
        "script": "Editing Script",
        "instructions": "Edit Markdown",
        "json_schema": "Edit JSON Schema",
        "message": "Message Editor",
        "call_activity": "Select Process Model",
    },
    "script_editor": {
        "mode": "monaco",
        "apply_button": "close",
        "close_button": "close",
    },
    "message_editor": {"opens": True},
    "call_activity": {"allow_same_process_id": True},
    "call_activity_dialog_closes": False,
}
