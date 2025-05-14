import re

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

