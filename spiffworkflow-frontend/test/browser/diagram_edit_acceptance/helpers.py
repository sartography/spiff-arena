import re
from typing import Any, Mapping

from playwright.sync_api import Locator, Page, expect

from diagram_edit_acceptance.config import CONFIG


def _locator(parent: Page | Locator, spec: Any) -> Locator:
    if isinstance(spec, Mapping):
        if "role" in spec:
            return parent.get_by_role(
                spec["role"],
                name=spec.get("name"),
                exact=spec.get("exact", False),
            )
        if "label" in spec:
            return parent.get_by_label(spec["label"])
        if "text" in spec:
            return parent.get_by_text(spec["text"])
        if "css" in spec:
            return parent.locator(spec["css"])
    return parent.locator(spec)


def locate(page: Page, spec: Any, container: Locator | None = None) -> Locator:
    return _locator(container or page, spec)


def get_save_button(page: Page) -> Locator:
    save_config = CONFIG.get("save_button", {})
    test_id = save_config.get("test_id")
    if test_id:
        return page.get_by_test_id(test_id)
    return page.get_by_role("button", name=save_config.get("role_name", "Save"))


def open_diagram(page: Page, element_id: str) -> None:
    diagram_config = CONFIG["diagram"]
    page.set_viewport_size({"width": 1600, "height": 2000})
    page.goto(diagram_config["url"])

    loaded_text = diagram_config.get("loaded_text")
    if loaded_text:
        expect(page.get_by_text(loaded_text), "Diagram loaded").to_be_visible(
            timeout=20000
        )

    fit_button = _locator(page, diagram_config["fit_button"])
    fit_button.click()

    expect(
        page.locator(f'g[data-element-id="{element_id}"]'),
        "Element rendered",
    ).to_be_visible(timeout=20000)


def _element_selected(page: Page, element_id: str) -> bool:
    input_id = page.locator('input[name="id"]')
    if input_id.count() > 0:
        return input_id.input_value() == element_id
    return page.evaluate(
        """(id) => {
        const el = document.querySelector(`g[data-element-id=\"${id}\"]`);
        return el ? el.classList.contains('selected') : false;
      }""",
        element_id,
    )


def select_element(page: Page, element_id: str) -> None:
    target = page.locator(f'g[data-element-id="{element_id}"]')
    label = target.locator(".djs-label")
    hit = target.locator(".djs-hit")

    for _ in range(4):
        page.evaluate(
            """(id) => {
            const el = document.querySelector(`g[data-element-id=\"${id}\"]`);
            if (el) el.scrollIntoView({ block: 'center', inline: 'center' });
          }""",
            element_id,
        )
        if label.count() > 0:
            label.first.click(force=True)
        elif hit.count() > 0:
            hit.first.click(force=True)
        else:
            target.click(force=True)

        if _element_selected(page, element_id):
            return

        page.wait_for_timeout(250)
        page.evaluate(
            """(id) => {
            const el = document.querySelector(`g[data-element-id=\"${id}\"]`);
            if (!el) return false;
            ['mousedown','mouseup','click'].forEach((type) =>
              el.dispatchEvent(new MouseEvent(type, { bubbles: true }))
            );
            return true;
          }""",
            element_id,
        )
        if _element_selected(page, element_id):
            return
        page.wait_for_timeout(250)

    expect(
        page.locator(f'g[data-element-id="{element_id}"]'),
        "Diagram element selected",
    ).to_have_class(re.compile(r"\bselected\b"), timeout=10000)


def expand_group_if_needed(group_locator: Locator) -> None:
    launch_button = group_locator.locator('button:has-text("Launch Editor")')
    if not launch_button.is_visible():
        try:
            group_locator.evaluate(
                """(group) => {
                const toggle = group.querySelector('button[title="Toggle section"]');
                toggle?.click();
                }"""
            )
            return
        except Exception:
            pass
        toggle = group_locator.locator('button[title="Toggle section"]')
        if toggle.count() > 0:
            toggle.first.click(force=True)
            return
        header = group_locator.locator('.bio-properties-panel-group-header-title')
        if header.count() > 0:
            header.first.click(force=True)


def ensure_group_visible(page: Page, element_id: str, group_id: str) -> None:
    for _ in range(3):
        select_element(page, element_id)
        if page.locator(f'[data-group-id="{group_id}"]').count() > 0:
            return
        page.wait_for_timeout(300)
    expect(
        page.locator(f'[data-group-id="{group_id}"]'),
        f"{group_id} group visible",
    ).to_be_visible(timeout=10000)


def open_and_close_dialog(page: Page, heading_text: str) -> None:
    dialog = page.get_by_role("dialog")
    expect(
        dialog.get_by_role("heading", name=re.compile(heading_text, re.I)),
        "Dialog opened",
    ).to_be_visible(timeout=10000)
    close_button = dialog.get_by_role(
        "button", name=re.compile(r"(close|cancel|dismiss)", re.I)
    )
    if close_button.is_visible():
        close_button.click()
    else:
        page.keyboard.press("Escape")
    expect(dialog, "Dialog closed").to_be_hidden(timeout=10000)


def open_script_editor(page: Page) -> Locator:
    group_id = CONFIG["groups"]["script"]
    group = page.locator(f'[data-group-id="{group_id}"]')
    page.wait_for_selector(f'[data-group-id="{group_id}"]', timeout=10000)
    expect(group, "Script properties visible").to_be_visible(timeout=10000)
    expand_group_if_needed(group)
    launch_button = _locator(group, CONFIG["selectors"]["script_launch"])
    launch_button.click(force=True)

    dialog = page.get_by_role("dialog")
    expect(
        dialog.get_by_role(
            "heading", name=re.compile(CONFIG["dialog_headings"]["script"], re.I)
        ),
        "Script editor dialog opened",
    ).to_be_visible(timeout=10000)
    return dialog


def read_script_text(dialog: Locator) -> str:
    mode = CONFIG["script_editor"]["mode"]
    if mode == "textarea":
        return dialog.locator("textarea").first.input_value().strip()
    text = dialog.locator(".view-lines").inner_text().strip()
    return text.replace("\u00a0", " ")


def set_script_text(page: Page, dialog: Locator, text: str) -> None:
    mode = CONFIG["script_editor"]["mode"]
    if mode == "textarea":
        dialog.locator("textarea").first.fill(text)
        return
    editor = dialog.locator(".monaco-editor")
    editor.click()
    page.keyboard.press("Meta+A")
    page.keyboard.press("Backspace")
    page.keyboard.insert_text(text)


def close_script_editor(page: Page, dialog: Locator, action: str) -> None:
    button_label = CONFIG["script_editor"].get(action, action)
    dialog.get_by_role("button", name=re.compile(button_label, re.I)).click()


def open_message_editor(page: Page) -> Locator | None:
    group_id = CONFIG["groups"]["message"]
    group = page.locator(f'[data-group-id="{group_id}"]')
    expect(group, "Message group visible").to_be_visible(timeout=10000)
    expand_group_if_needed(group)

    button = _locator(group, CONFIG["selectors"]["message_open"])
    expect(button, "Open message editor button visible").to_be_visible(timeout=10000)
    expect(button, "Open message editor button enabled").to_be_enabled(timeout=10000)

    if not CONFIG.get("message_editor", {}).get("opens", True):
        return None

    button.click(force=True)
    dialog = page.get_by_role("dialog")
    expect(
        dialog.get_by_role(
            "heading", name=re.compile(CONFIG["dialog_headings"]["message"], re.I)
        ),
        "Message editor dialog opened",
    ).to_be_visible(timeout=10000)
    return dialog
