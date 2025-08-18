import datetime
import json
import logging
import os
import time
import uuid

from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException
from SpiffWorkflow.bpmn.parser.util import full_tag
from SpiffWorkflow.bpmn.script_engine import PythonScriptEngine, TaskDataEnvironment
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.spiff.parser.process import SpiffBpmnParser
from SpiffWorkflow.spiff.parser.task_spec import ServiceTaskParser, SpiffTaskParser
from SpiffWorkflow.spiff.serializer.config import SPIFF_CONFIG
from SpiffWorkflow.spiff.serializer.task_spec import ServiceTaskConverter, SpiffBpmnTaskConverter
from SpiffWorkflow.spiff.specs.defaults import CallActivity, ManualTask, NoneTask, ServiceTask, UserTask
from SpiffWorkflow.spiff.specs.spiff_task import SpiffBpmnTask
from SpiffWorkflow.task import Task
from SpiffWorkflow.util.task import TaskFilter, TaskState

logging.basicConfig(level=logging.INFO)

class CustomManualTask(ManualTask):
    def _run(self, task):
        super()._run(task)
        return None

class CustomManualTaskConverter(SpiffBpmnTaskConverter):
    def __init__(self, target_class, registry, typename = "ManualTask"):
        super().__init__(target_class, registry, typename)

class CustomNoneTask(NoneTask):
    def _run(self, task):
        super()._run(task)
        return None

class CustomNoneTaskConverter(SpiffBpmnTaskConverter):
    def __init__(self, target_class, registry, typename = "NoneTask"):
        super().__init__(target_class, registry, typename)

class CustomServiceTask(ServiceTask):
    def _execute(self, task):
        super()._execute(task)
        return None

class CustomServiceTaskConverter(ServiceTaskConverter):
    def __init__(self, target_class, registry, typename = "ServiceTask"):
        super().__init__(target_class, registry, typename)

class CustomUserTask(UserTask):
    def _run(self, task):
        super()._run(task)
        return None

class CustomUserTaskConverter(SpiffBpmnTaskConverter):
    def __init__(self, target_class, registry, typename = "UserTask"):
        super().__init__(target_class, registry, typename)

class CustomParser(SpiffBpmnParser):
    OVERRIDE_PARSER_CLASSES = SpiffBpmnParser.OVERRIDE_PARSER_CLASSES
    OVERRIDE_PARSER_CLASSES.update({full_tag("manualTask"): (SpiffTaskParser, CustomManualTask)})
    OVERRIDE_PARSER_CLASSES.update({full_tag("task"): (SpiffTaskParser, CustomNoneTask)})
    OVERRIDE_PARSER_CLASSES.update({full_tag("serviceTask"): (ServiceTaskParser, CustomServiceTask)})
    OVERRIDE_PARSER_CLASSES.update({full_tag("userTask"): (SpiffTaskParser, CustomUserTask)})


SPIFF_CONFIG[CustomManualTask] = CustomManualTaskConverter
SPIFF_CONFIG[CustomNoneTask] = CustomNoneTaskConverter
SPIFF_CONFIG[CustomServiceTask] = CustomServiceTaskConverter
SPIFF_CONFIG[CustomUserTask] = CustomUserTaskConverter

del SPIFF_CONFIG[ManualTask]
del SPIFF_CONFIG[NoneTask]
del SPIFF_CONFIG[ServiceTask]
del SPIFF_CONFIG[UserTask]

class CustomEnvironment(TaskDataEnvironment):
    def __init__(self):
        # TODO: would be nice to get these from the client so we don't have to code change for globals
        super().__init__(environment_globals={
            "datetime": datetime.datetime,
            "json": json,
            "time": time,
            "timedelta": datetime.timedelta,
        })

    def execute(self, script, context, external_context=None):
        if external_context is None:
            external_context = {}
        
        # TODO: would be nice to get these from the client so we don't have to code change for globals
        external_context["get_task_data_value"] = lambda k, d=None: context.get(k, d)
        external_context["get_top_level_process_info"] = lambda: {
            "process_instance_id": 0,
            "process_model_identifier": "local",
        }
        
        return super().execute(script or "", context, external_context)


custom_environment = CustomEnvironment()


class CustomScriptEngine(PythonScriptEngine):
    def __init__(self):
        super().__init__(environment=custom_environment)

    def call_service(
        self,
        context,
        **kwargs,
    ):
        operation_name = kwargs.get("operation_name")
        task_data = context.data
        
        operation_params = kwargs.get("operation_params", {})
        operation_params = {k: v["value"] for k, v in operation_params.items()}
        operation_params["spiff__task_data"] = task_data
        
        return json.dumps({
            "operation_name": operation_name,
            "operation_params": operation_params,
            "task_data": task_data,
        })


registry = BpmnWorkflowSerializer.configure(SPIFF_CONFIG)
serializer = BpmnWorkflowSerializer(registry=registry)

def specs_from_xml(files):
    parser = CustomParser()

    for file in files:
        if file[0].endswith(".bpmn"):
            parser.add_bpmn_str(file[1].encode("utf-8"))
        elif file[0].endswith(".dmn"):
            parser.add_dmn_str(file[1].encode("utf-8"))

    try:
        all_specs = parser.find_all_specs()
    except Exception as e:
        return None, f"{e.__class__.__name__}: {e}"
    
    process_id = parser.get_process_ids()[0]
    process = all_specs.pop(process_id)
    subprocesses = all_specs

    workflow = BpmnWorkflow(process, subprocesses)
    workflow_dct = serializer.to_dict(workflow)
    workflow_specs_dct = {
        "serializer_version": "spiff-runner-1",
        "spec": workflow_dct["spec"],
        "subprocess_specs": workflow_dct["subprocess_specs"],
    }

    return json.dumps(workflow_specs_dct), None

def hydrate_workflow(specs, state):
    specs = serializer.deserialize_json(specs)
    process = specs.pop("spec")
    subprocesses = specs.pop("subprocess_specs")

    if not state:
        workflow = BpmnWorkflow(process, subprocesses)
    else:
        state["spec"] = process
        state["subprocess_specs"] = subprocesses
        workflow = serializer.from_dict(state)

    workflow.script_engine = CustomScriptEngine()

    return workflow

def lazy_load_tasks(workflow):
    return get_tasks(
        workflow,
        TaskFilter(TaskState.DEFINITE_MASK | TaskState.FINISHED_MASK, spec_class=CallActivity),
    )

def missing_lazy_load_specs(workflow):
    for t in lazy_load_tasks(workflow):
        spec = t["task_spec"].get("spec")
        if not spec:
            continue
        if spec not in workflow.subprocess_specs:
            return True
    return False

def next_task(workflow, state):
    task_filter = TaskFilter(state=TaskState.READY)
    for task in workflow.get_tasks(task_filter=task_filter):
        return task
    return None

def _advance_workflow(workflow, task, strategy_name):
    iters = 0

    # TODO: make maxIters part of strategy
    while task and iters < 100:
        iters = iters + 1
        if task.state == TaskState.STARTED:
            task.complete()
        else:
            task.run()
        workflow.refresh_waiting_tasks()

        task = next_task(workflow, TaskState.READY)
        if not task:
            break
        elif strategy_name == "oneAtATime" and task.task_spec.bpmn_id:
            break
        elif strategy_name == "greedy":
            if task.task_spec.__class__.__name__.startswith("Custom"):
                break
            if missing_lazy_load_specs(workflow):
                break

    step = build_response(workflow, None)
    return step

def advance_workflow(specs, state, completed_task, strategy_name, start_params):
    workflow = hydrate_workflow(specs, state)
    if state == {} and start_params:
        for task in workflow.get_tasks(task_filter=TaskFilter(state=TaskState.READY, spec_name="Start")):
            task.data.update(start_params.get("data", {}))
            break
    
    if completed_task:
        task = workflow.get_task_from_id(uuid.UUID(completed_task["id"]))
        if "data" in completed_task:
            task.data.update(completed_task["data"])
    else:
        task = next_task(workflow, TaskState.READY)

    try:
        return _advance_workflow(workflow, task, strategy_name)
    except Exception as e:
        try:
            return build_response(workflow, e)
        except Exception as e:
            return json.dumps({ "status": "error", "message": f"{e}" })

def get_tasks(workflow, task_filter):
    tasks = workflow.get_tasks(task_filter=task_filter)

    spec_keys = set([
        "name", "description", "manual", "bpmn_id", "bpmn_name",
        "lane", "documentation", "extensions", "typename",
        "result_variable", "spec",
    ])

    return [{
        "id": str(t.id),
        "data": t.data,
        "bpmn_process_id": t.workflow.spec.name,
        "state": t.state,
        "task_spec": {
            k: v for k, v in serializer.to_dict(t.task_spec).items() if k in spec_keys
        },
    } for t in tasks]
    
def get_state(workflow):
    state = serializer.to_dict(workflow)
    state.pop("spec")
    state.pop("subprocess_specs")
    return state

def build_response(workflow, e):
    completed = workflow.completed

    if e is None:
        response = { "status": "ok", "completed": completed }
    else:
        response = {
            "status": "error",
            "message": f"{e}",
            "error_tasks": get_tasks(workflow, TaskFilter(TaskState.ERROR)),
        }

    if completed:
        response["result"] = workflow.data
    else:
        response["pending_tasks"] = get_tasks(
            workflow,
            TaskFilter(TaskState.STARTED | TaskState.READY | TaskState.WAITING),
        )
        response["lazy_load_tasks"] = lazy_load_tasks(workflow)

    response["state"] = get_state(workflow)

    return json.dumps(response)

