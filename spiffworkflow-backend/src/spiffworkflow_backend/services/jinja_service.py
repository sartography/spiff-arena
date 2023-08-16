import re
from sys import exc_info

import jinja2
from jinja2 import TemplateSyntaxError
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.services.task_service import TaskModelError
from spiffworkflow_backend.services.task_service import TaskService


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
        sanitized_value = re.sub(r"([|])", r"\\\1", value)
        return sanitized_value


class JinjaService:
    @classmethod
    def render_instructions_for_end_user(cls, task: TaskModel | SpiffTask, extensions: dict | None = None) -> str:
        """Assure any instructions for end user are processed for jinja syntax."""
        if extensions is None:
            if isinstance(task, TaskModel):
                extensions = TaskService.get_extensions_from_task_model(task)
            else:
                extensions = task.task_spec.extensions
        if extensions and "instructionsForEndUser" in extensions:
            if extensions["instructionsForEndUser"]:
                try:
                    instructions = cls.render_jinja_template(extensions["instructionsForEndUser"], task)
                    extensions["instructionsForEndUser"] = instructions
                    return instructions
                except TaskModelError as wfe:
                    wfe.add_note("Failed to render instructions for end user.")
                    raise ApiError.from_workflow_exception("instructions_error", str(wfe), exp=wfe) from wfe
        return ""

    @classmethod
    def render_jinja_template(cls, unprocessed_template: str, task: TaskModel | SpiffTask) -> str:
        jinja_environment = jinja2.Environment(autoescape=True, lstrip_blocks=True, trim_blocks=True)
        jinja_environment.filters.update(JinjaHelpers.get_helper_mapping())
        try:
            template = jinja_environment.from_string(unprocessed_template)
            if isinstance(task, TaskModel):
                data = task.get_data()
            else:
                data = task.data
            return template.render(**data, **JinjaHelpers.get_helper_mapping())
        except jinja2.exceptions.TemplateError as template_error:
            if isinstance(task, TaskModel):
                wfe = TaskModelError(str(template_error), task_model=task, exception=template_error)
            else:
                wfe = WorkflowTaskException(str(template_error), task=task, exception=template_error)
            if isinstance(template_error, TemplateSyntaxError):
                wfe.line_number = template_error.lineno
                wfe.error_line = template_error.source.split("\n")[template_error.lineno - 1]
            wfe.add_note("Jinja2 template errors can happen when trying to display task data")
            raise wfe from template_error
        except Exception as error:
            _type, _value, tb = exc_info()
            if isinstance(task, TaskModel):
                wfe = TaskModelError(str(error), task_model=task, exception=error)
            else:
                wfe = WorkflowTaskException(str(error), task=task, exception=error)
            while tb:
                if tb.tb_frame.f_code.co_filename == "<template>":
                    wfe.line_number = tb.tb_lineno
                    wfe.error_line = unprocessed_template.split("\n")[tb.tb_lineno - 1]
                tb = tb.tb_next
            wfe.add_note("Jinja2 template errors can happen when trying to display task data")
            raise wfe from error
