import re

import jinja2
from jinja2 import meta

class JinjaHelpers:
    """These are helpers that added to script tasks and to jinja for rendering templates.

    Can be used from a jinja template as a filter like:
        This is a template for {{ unsanitized_variable | sanitize_for_md }}.
    Or as a python-style method call like:
        This is a template for {{ sanitize_for_md(unsanitized_variable) }}.

    It can also be used from a script task like:
        sanitized_variable = sanitize_for_md(unsanitized_variable)
    """

    @classmethod
    def get_helper_mapping(cls) -> dict:
        """So we can use filter syntax in markdown."""
        return {"sanitize_for_md": JinjaHelpers.sanitize_for_md}

    @classmethod
    def sanitize_for_md(cls, value: str) -> str:
        """Sanitizes given value for markdown."""
        # modified from https://github.com/python-telegram-bot/python-telegram-bot/blob/1fdaaac8094c9d76c34c8c8e8c9add16080e75e7/telegram/utils/helpers.py#L149
        #
        # > was in this list but was removed because it doesn't seem to cause any
        # issues and if it is in the list it prints like "&gt;" instead
        escape_chars = r"_*[]()~`#+-=|{}!"
        escaped_value = re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", value)
        escaped_value = escaped_value.replace("\n", "").replace("\r", "")
        return escaped_value


def jinja(s, data):
    if not s:
        return s, None

    try:
        env = jinja2.Environment(autoescape=True, lstrip_blocks=True, trim_blocks=True)
        env.filters.update(JinjaHelpers.get_helper_mapping())
        template = env.from_string(s)

        return template.render(**data), None
    except jinja2.TemplateSyntaxError as e:
        error_msg = f"{e.__class__.__name__}: {e}"
        if e.lineno is not None:
            lines = s.splitlines()
            if 0 < e.lineno <= len(lines):
                error_msg += f"\n  Line {e.lineno}: {lines[e.lineno - 1].strip()}"
        return None, error_msg
    except Exception as e:
        error_msg = f"{e.__class__.__name__}: {e}"
        if isinstance(e, TypeError) and "Undefined" in str(e):
            referenced_vars = meta.find_undeclared_variables(env.parse(s))
            undefined_vars = referenced_vars - set(data.keys())
            if undefined_vars:
                names = ", ".join(sorted(undefined_vars))
                error_msg += f"\n  Undefined variables: {names}"
        if hasattr(e, "lineno") and e.lineno is not None:
            lines = s.splitlines()
            if 0 < e.lineno <= len(lines):
                error_msg += f"\n  Line {e.lineno}: {lines[e.lineno - 1].strip()}"
        return None, error_msg
