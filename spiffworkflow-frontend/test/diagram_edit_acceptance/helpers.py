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
    return page.get_by_role("button", name="Save")  # Both apps use "Save"


def open_diagram(page: Page, element_id: str) -> None:
    diagram_config = CONFIG["diagram"]
    page.set_viewport_size({"width": 1600, "height": 2000})
    page.goto(diagram_config["url"])

    loaded_text = diagram_config.get("loaded_text")
    if loaded_text:
        # Check for the file chip that displays the loaded diagram name
        file_chip_selector = diagram_config.get("file_chip_selector")
        if file_chip_selector:
            chip = page.locator(file_chip_selector).filter(has_text=loaded_text)
            expect(chip, "File chip visible").to_be_visible(timeout=20000)

    fit_button = _locator(page, diagram_config["fit_button"])
    expect(fit_button, "Fit button visible").to_be_visible(timeout=20000)
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
    hit = target.locator(".djs-hit")
    label = target.locator(".djs-label")

    expect(target, "Diagram element visible").to_be_visible(timeout=20000)

    for _ in range(4):
        page.evaluate(
            """(id) => {
            const el = document.querySelector(`g[data-element-id=\"${id}\"]`);
            if (el) el.scrollIntoView({ block: 'center', inline: 'center' });
          }""",
            element_id,
        )
        if hit.count() > 0:
            hit.first.dispatch_event("mousedown")
            hit.first.dispatch_event("mouseup")
            hit.first.dispatch_event("click")
        elif label.count() > 0:
            label.first.dispatch_event("mousedown")
            label.first.dispatch_event("mouseup")
            label.first.dispatch_event("click")
        else:
            target.dispatch_event("mousedown")
            target.dispatch_event("mouseup")
            target.dispatch_event("click")

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
    expect(group_locator, "Group visible").to_be_visible(timeout=10000)
    action = group_locator.evaluate(
        """(groupEl) => {
        const button = groupEl.querySelector('button[title="Toggle section"]');
        const entries = groupEl.querySelector('.bio-properties-panel-group-entries');
        if (entries && entries.offsetParent !== null) {
          return "already";
        }
        if (button) {
          const expanded = button.getAttribute('aria-expanded');
          if (expanded && expanded !== "false") {
            return "already";
          }
          button.click();
          return "toggle";
        }
        const header = groupEl.querySelector('.bio-properties-panel-group-header-title');
        if (header) {
          header.click();
          return "header";
        }
        return null;
      }"""
    )
    assert action, "Group toggle or header available"


def expand_entry_if_needed(entry_locator: Locator) -> None:
    entry_locator.wait_for(state="attached", timeout=10000)
    inputs = entry_locator.locator("input, textarea")
    if inputs.count() > 0 and inputs.first.is_visible():
        return
    if entry_locator.is_visible():
        entry_locator.scroll_into_view_if_needed()
    entry_locator.evaluate(
        """(entryEl) => {
        const toggle = entryEl.querySelector('button[title="Toggle list item"]');
        if (toggle) {
          toggle.click();
          return;
        }
        const header = entryEl.querySelector('.bio-properties-panel-collapsible-entry-header');
        header?.click();
        }"""
    )


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
    group_id = "group-spiff_script"
    page.wait_for_function(
        """(groupId) => !!document.querySelector(`[data-group-id="${groupId}"]`)""",
        arg=group_id,
    )
    page.evaluate(
        """(groupId) => {
        const groupEl = document.querySelector(`[data-group-id="${groupId}"]`);
        if (!groupEl) return;
        const toggle = groupEl.querySelector('button[title="Toggle section"]');
        if (toggle) {
          toggle.click();
        }
        const button = Array.from(groupEl.querySelectorAll('button'))
          .find((btn) => btn.textContent?.trim() === 'Launch Editor');
        if (button) {
          button.click();
        }
        }""",
        group_id,
    )

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
    page.keyboard.press("ControlOrMeta+A")
    page.keyboard.press("Backspace")
    page.keyboard.insert_text(text)


def close_script_editor(page: Page, dialog: Locator, action: str) -> None:
    button_label = CONFIG["script_editor"].get(action, action)
    dialog.get_by_role("button", name=re.compile(button_label, re.I)).click()


def open_message_editor(page: Page) -> Locator | None:
    group_id = "group-messages"
    group = page.locator(f'[data-group-id="{group_id}"]').or_(
        page.locator('[data-group-id]').filter(
            has=_locator(page, CONFIG["selectors"]["message_open"])
        )
    ).first
    expect(group, "Message group visible").to_be_visible(timeout=10000)
    expand_group_if_needed(group)

    button = _locator(group, CONFIG["selectors"]["message_open"])
    expect(button, "Open message editor button visible").to_be_visible(timeout=10000)
    expect(button, "Open message editor button enabled").to_be_enabled(timeout=10000)

    if not CONFIG.get("message_editor", {}).get("opens", True):
        return None

    group.evaluate(
        """(groupEl) => {
        const button = Array.from(groupEl.querySelectorAll('button'))
          .find((btn) => /open/i.test(btn.textContent || ''));
        button?.click();
        }"""
    )
    dialog = page.get_by_role("dialog")
    expect(
        dialog.get_by_role(
            "heading", name=re.compile("Message Editor", re.I)
        ),
        "Message editor dialog opened",
    ).to_be_visible(timeout=10000)
    return dialog
