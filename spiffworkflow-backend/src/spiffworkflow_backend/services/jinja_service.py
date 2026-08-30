import json
from sys import exc_info

import jinja2
from jinja2 import TemplateSyntaxError
from spiff_arena_common.jinja import JinjaHelpers
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.models.task_instructions_for_end_user import TaskInstructionsForEndUserModel
from spiffworkflow_backend.services.task_service import TaskModelError
from spiffworkflow_backend.services.task_service import TaskService


class JinjaService:
    @classmethod
    def render_instructions_for_end_user(
        cls, task: TaskModel | SpiffTask | None = None, extensions: dict | None = None, task_data: dict | None = None
    ) -> str:
        """Assure any instructions for end user are processed for jinja syntax."""
        if extensions is None:
            if isinstance(task, TaskModel):
                extensions = TaskService.get_extensions_from_task_model(task)
            elif task and hasattr(task.task_spec, "extensions"):
                extensions = task.task_spec.extensions
        if extensions and "instructionsForEndUser" in extensions:
            if extensions["instructionsForEndUser"]:
                try:
                    return cls.render_jinja_template(extensions["instructionsForEndUser"], task, task_data=task_data)
                except TaskModelError as wfe:
                    wfe.add_note("Failed to render instructions for end user.")
                    raise ApiError.from_workflow_exception("instructions_error", str(wfe), exp=wfe) from wfe
        return ""

    @classmethod
    def render_jinja_template(
        cls, unprocessed_template: str, task: TaskModel | SpiffTask | None = None, task_data: dict | None = None
    ) -> str:
        jinja_environment = jinja2.Environment(autoescape=True, lstrip_blocks=True, trim_blocks=True)
        jinja_environment.filters.update(JinjaHelpers.get_helper_mapping())
        try:
            template = jinja_environment.from_string(unprocessed_template)
            if task_data is not None:
                data = task_data
            elif isinstance(task, TaskModel):
                data = task.get_data()
            elif task is not None:
                data = task.data
            else:
                raise ValueError("No task or task data provided to render_jinja_template")

            return template.render(**data, **JinjaHelpers.get_helper_mapping())
        except jinja2.exceptions.TemplateError as template_error:
            if task is None:
                raise template_error
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
            if task is None:
                raise error
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

    @classmethod
    def add_instruction_for_end_user_if_appropriate(
        cls, spiff_tasks: list[SpiffTask], process_instance_id: int, tasks_that_have_been_seen: set[str]
    ) -> None:
        for spiff_task in spiff_tasks:
            if spiff_task.task_spec.manual:
                continue
            if hasattr(spiff_task.task_spec, "extensions") and spiff_task.task_spec.extensions.get(
                "instructionsForEndUser", None
            ):
                task_guid = str(spiff_task.id)
                if task_guid in tasks_that_have_been_seen:
                    continue
                instruction_template = spiff_task.task_spec.extensions["instructionsForEndUser"]
                instruction = JinjaService.render_instructions_for_end_user(spiff_task)
                if instruction != "":
                    process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
                    task_data = {key: value for key, value in spiff_task.data.items() if cls._is_jsonable(value)}
                    TaskInstructionsForEndUserModel.insert_or_update_record(
                        task_guid=str(spiff_task.id),
                        process_instance_id=process_instance_id,
                        instruction=instruction,
                        instruction_template=instruction_template,
                        task_data=task_data,
                        process_model_identifier=(process_instance.process_model_identifier if process_instance else None),
                        bpmn_file_name=getattr(spiff_task.workflow.spec, "file", None),
                        bpmn_process_identifier=spiff_task.workflow.spec.name,
                        task_bpmn_identifier=spiff_task.task_spec.bpmn_id,
                        source_artifact_ref=(process_instance.source_artifact_ref if process_instance else None),
                        bpmn_version_control_identifier=(
                            process_instance.bpmn_version_control_identifier if process_instance else None
                        ),
                    )
                    tasks_that_have_been_seen.add(str(spiff_task.id))

    @staticmethod
    def _is_jsonable(value: object) -> bool:
        try:
            json.dumps(value)
            return True
        except (TypeError, OverflowError, ValueError):
            return False

    @classmethod
    def render_queued_instruction(
        cls,
        queued_instruction: TaskInstructionsForEndUserModel,
        translated_template: str | None = None,
    ) -> str:
        template = translated_template if translated_template is not None else queued_instruction.instruction_template
        if template is None or queued_instruction.task_data is None:
            return queued_instruction.instruction
        return cls.render_jinja_template(template, task_data=queued_instruction.task_data)
