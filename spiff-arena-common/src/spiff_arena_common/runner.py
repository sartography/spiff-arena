import base64
import calendar
import datetime
import gzip
import json
import logging
import time
import uuid

import jsonschema

from spiff_arena_common.data_stores import JSONFileDataStore

from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException
from SpiffWorkflow.bpmn.specs.mixins.multiinstance_task import LoopTask
from SpiffWorkflow.bpmn.parser.util import full_tag
from SpiffWorkflow.bpmn.script_engine import PythonScriptEngine, TaskDataEnvironment
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.spiff.parser.process import SpiffBpmnParser
from SpiffWorkflow.spiff.parser.event_parsers import SpiffReceiveTaskParser, SpiffSendTaskParser
from SpiffWorkflow.spiff.parser.task_spec import ServiceTaskParser, SpiffTaskParser
from SpiffWorkflow.spiff.serializer.config import SPIFF_CONFIG
from SpiffWorkflow.spiff.serializer.task_spec import SendReceiveTaskConverter, ServiceTaskConverter, SpiffBpmnTaskConverter
from SpiffWorkflow.spiff.specs.defaults import CallActivity, ManualTask, NoneTask, ReceiveTask, SendTask, ServiceTask, UserTask
from SpiffWorkflow.util.task import TaskFilter, TaskState

logging.basicConfig(level=logging.ERROR)

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

class CustomReceiveTask(ReceiveTask):
    def _update_hook(self, my_task):
        # Bypass event waiting — go straight to READY so the UI can show a form
        return True

    def _run(self, my_task):
        return None

class CustomReceiveTaskConverter(SendReceiveTaskConverter):
    def __init__(self, target_class, registry, typename = "ReceiveTask"):
        super().__init__(target_class, registry, typename)

class CustomSendTask(SendTask):
    def _run(self, my_task):
        return None

class CustomSendTaskConverter(SendReceiveTaskConverter):
    def __init__(self, target_class, registry, typename = "SendTask"):
        super().__init__(target_class, registry, typename)

class CustomParser(SpiffBpmnParser):
    DATA_STORE_CLASSES = {
        "JSONFileDataStore": JSONFileDataStore,
    }
    
    OVERRIDE_PARSER_CLASSES = SpiffBpmnParser.OVERRIDE_PARSER_CLASSES
    OVERRIDE_PARSER_CLASSES.update({full_tag("manualTask"): (SpiffTaskParser, CustomManualTask)})
    OVERRIDE_PARSER_CLASSES.update({full_tag("task"): (SpiffTaskParser, CustomNoneTask)})
    OVERRIDE_PARSER_CLASSES.update({full_tag("serviceTask"): (ServiceTaskParser, CustomServiceTask)})
    OVERRIDE_PARSER_CLASSES.update({full_tag("userTask"): (SpiffTaskParser, CustomUserTask)})
    OVERRIDE_PARSER_CLASSES.update({full_tag("receiveTask"): (SpiffReceiveTaskParser, CustomReceiveTask)})
    OVERRIDE_PARSER_CLASSES.update({full_tag("sendTask"): (SpiffSendTaskParser, CustomSendTask)})


SPIFF_CONFIG[CustomManualTask] = CustomManualTaskConverter
SPIFF_CONFIG[CustomNoneTask] = CustomNoneTaskConverter
SPIFF_CONFIG[CustomServiceTask] = CustomServiceTaskConverter
SPIFF_CONFIG[CustomUserTask] = CustomUserTaskConverter
SPIFF_CONFIG[CustomReceiveTask] = CustomReceiveTaskConverter
SPIFF_CONFIG[CustomSendTask] = CustomSendTaskConverter

del SPIFF_CONFIG[ManualTask]
del SPIFF_CONFIG[NoneTask]
del SPIFF_CONFIG[ServiceTask]
del SPIFF_CONFIG[UserTask]
del SPIFF_CONFIG[ReceiveTask]
del SPIFF_CONFIG[SendTask]

class CustomEnvironment(TaskDataEnvironment):
    def __init__(self):
        # TODO: would be nice to get these from the client so we don't have to code change for globals
        super().__init__(environment_globals={
            "calendar": calendar,
            "datetime": datetime.datetime,
            "json": json,
            "jsonschema": jsonschema,
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

# Global workflow cache by session_id to avoid repeated (de)serialization
_workflow_cache = {}

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

def hydrate_workflow(specs, state, session_id=None):
    """Hydrate workflow from specs and state, using cache when available.

    Args:
        specs: JSON string or dict of workflow specs
        state: dict, str (base64-encoded gzip-compressed), or None
        session_id: Optional session ID for caching

    Returns:
        BpmnWorkflow instance
    """
    # If we have a cached workflow and state is None, just return the cache
    if session_id and state is None and session_id in _workflow_cache:
        return _workflow_cache[session_id]

    # Check cache when state is provided (state surgery case)
    if session_id and state and session_id in _workflow_cache:
        cached_workflow = _workflow_cache[session_id]

        # Decompress state if it's compressed
        if isinstance(state, str) and not state.startswith('{'):
            compressed = base64.b64decode(state)
            decompressed = gzip.decompress(compressed)
            state = json.loads(decompressed.decode('utf-8'))

        # Update cached workflow with new state (in-place mutation)
        # Only update the mutable parts - tasks, data, etc.
        cached_state = serializer.to_dict(cached_workflow)
        if state != cached_state:
            # State changed, need to deserialize
            specs_dict = serializer.deserialize_json(specs)
            process = specs_dict.pop("spec")
            subprocesses = specs_dict.pop("subprocess_specs")
            state["spec"] = process
            state["subprocess_specs"] = subprocesses
            workflow = serializer.from_dict(state)
            workflow.script_engine = CustomScriptEngine()
            _workflow_cache[session_id] = workflow
            return workflow

        return cached_workflow

    # Cache miss or no session_id - create new workflow
    specs_dict = serializer.deserialize_json(specs)
    process = specs_dict.pop("spec")
    subprocesses = specs_dict.pop("subprocess_specs")

    # Check if state is minimal state (only tasks/subprocesses, no workflow internals)
    # Minimal state can't be used for hydration - treat as empty
    is_minimal_state = (state and isinstance(state, dict) and
                       set(state.keys()) == {'tasks', 'subprocesses'} and
                       all(set(task.keys()) == {'task_spec', 'state'}
                           for task in state.get('tasks', {}).values()))

    if not state or is_minimal_state:
        workflow = BpmnWorkflow(process, subprocesses)
    else:
        # Handle base64-encoded gzip-compressed state (string)
        if isinstance(state, str) and not state.startswith('{'):
            # Decode base64 then decompress
            compressed = base64.b64decode(state)
            decompressed = gzip.decompress(compressed)
            state = json.loads(decompressed.decode('utf-8'))

        state["spec"] = process
        state["subprocess_specs"] = subprocesses
        workflow = serializer.from_dict(state)

    workflow.script_engine = CustomScriptEngine()

    # Cache the workflow if session_id provided
    if session_id:
        _workflow_cache[session_id] = workflow

    return workflow

def lazy_loads(workflow):
    specs = set()
    for t in workflow.get_tasks(task_filter=TaskFilter(spec_class=CallActivity)):
        specs.add(t.task_spec.spec)
    for t in workflow.get_tasks(task_filter=TaskFilter(spec_class=LoopTask)):
        task_spec = t.workflow.spec.task_specs.get(t.task_spec.task_spec)
        if task_spec and hasattr(task_spec, "spec"):
            specs.add(task_spec.spec)
    return list(specs)


def next_task(workflow, state, from_task=None):
    """Find the next task in the given state.

    Args:
        workflow: The workflow to search
        state: TaskState to filter by
        from_task: Optional task to start searching from (instead of root)

    Returns:
        The next task, or None if not found
    """
    task_filter = TaskFilter(state=state)
    for task in workflow.get_tasks(first_task=from_task, task_filter=task_filter):
        return task
    return None

def _advance_workflow(workflow, task, strategy_name, compress_state=False):
    iters = 0
    lazy_loads_list = None

    # Cache fixture file for unittest strategy to avoid repeated file I/O
    cached_fixture = None
    cached_fixture_file = None
    if strategy_name == "unittest" and task:
        fixture_file = task.data.get("spiff_testFixture_file")
        if fixture_file:
            try:
                with open(fixture_file) as f:
                    cached_fixture = json.load(f)
                cached_fixture_file = fixture_file
            except Exception as e:
                raise Exception(f"Failed to load test fixture from {fixture_file}: {e}") from e

    # TODO: make maxIters part of strategy, add cycle detection
    while task and iters < 5000:
        iters = iters + 1

        # Report progress every 50 iterations for UI feedback
        if iters % 50 == 0:
            print(f"[progress] iteration: {iters}", flush=True)

        if task.state == TaskState.STARTED:
            task.complete()
        else:
            task.run()

        # Only check for missing lazy loads if not using file-based test fixtures
        # (file fixtures preload all specs recursively, so this check is redundant and expensive)
        if not (strategy_name == "unittest" and cached_fixture_file):
            lazy_loads_list = lazy_loads(workflow)
            if any(spec not in workflow.subprocess_specs for spec in lazy_loads_list):
                break

        # Optimization: try searching from completed task first (fast path),
        # only refresh waiting tasks if fast path fails (deferred refresh)
        completed_task = task
        task = next_task(workflow, TaskState.READY, completed_task)
        if not task:
            workflow.refresh_waiting_tasks()
            task = next_task(workflow, TaskState.READY)
        if not task:
            break
        elif strategy_name == "oneAtATime" and task.task_spec.bpmn_id:
            break
        elif strategy_name == "greedy":
            if task.task_spec.__class__.__name__.startswith("Custom"):
                break
        elif strategy_name == "unittest":
            if task.task_spec.__class__.__name__.startswith("Custom"):
                # Check for file-based fixture first (ed recording playback)
                fixture_file = task.data.get("spiff_testFixture_file")
                if fixture_file:
                    # Use cached fixture data instead of re-reading from disk
                    if cached_fixture_file != fixture_file or cached_fixture is None:
                        # Fixture file changed or wasn't cached - shouldn't happen but handle it
                        try:
                            with open(fixture_file) as f:
                                cached_fixture = json.load(f)
                            cached_fixture_file = fixture_file
                        except Exception as e:
                            raise Exception(f"Failed to load test fixture from {fixture_file}: {e}") from e

                    stack = cached_fixture.get("pendingTaskStack", [])

                    if "spiff_testFixture_index" not in workflow.data:
                        index = len(stack) - 1
                    else:
                        index = workflow.data["spiff_testFixture_index"]

                    # If recording is exhausted (index < 0), let task run interactively
                    if index < 0:
                        break

                    if index >= len(stack):
                        break

                    expected = stack[index]
                    if task.task_spec.name != expected["id"]:
                        break

                    task.run()
                    task.data.update(expected["data"])
                    workflow.data["spiff_testFixture_index"] = index - 1
                else:
                    # Fallback to inline fixture (process-models compatibility)
                    stack = task.data.get("spiff_testFixture", {}).get("pendingTaskStack", [])
                    if not stack:
                        break
                    expected = stack.pop()
                    if task.task_spec.name != expected["id"]:
                        break
                    task.run()
                    task.data.update(expected["data"])
    return build_response(workflow, None, compress_state=compress_state, lazy_loads_result=lazy_loads_list)

def advance_workflow(specs, state, completed_task, strategy_name, start_params, compress_state=False, session_id=None):
    workflow = hydrate_workflow(specs, state, session_id=session_id)
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
        return _advance_workflow(workflow, task, strategy_name, compress_state=compress_state)
    except Exception as e:
        try:
            return build_response(workflow, e, compress_state=compress_state)
        except Exception as e2:
            return json.dumps({ "status": "error", "message": f"{e}" })

def get_tasks(workflow, task_filter):
    tasks = workflow.get_tasks(task_filter=task_filter)

    spec_keys = set([
        "name", "description", "manual", "bpmn_id", "bpmn_name",
        "lane", "documentation", "extensions", "typename",
        "result_variable", "spec", "event_definition",
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
    
def get_state(workflow, compress=False):
    """Get workflow state, optionally compressed with gzip.

    Args:
        workflow: The workflow to serialize
        compress: If True, return base64-encoded gzip-compressed string. If False, return dict.

    Returns:
        str (base64-encoded compressed, if compress=True) or dict (if compress=False)
    """
    state = serializer.to_dict(workflow)
    state.pop("spec")
    state.pop("subprocess_specs")

    if compress:
        json_str = json.dumps(state)
        compressed = gzip.compress(json_str.encode('utf-8'))
        # Base64 encode for JSON serialization
        return base64.b64encode(compressed).decode('ascii')

    return state

def get_minimal_state(workflow):
    """Get minimal state needed for diagram coloring (task_spec and state only).

    Args:
        workflow: The workflow to extract state from

    Returns:
        dict with tasks and subprocesses containing only {task_spec, state} fields
    """
    # Extract minimal task info: just task_spec ID and state
    tasks = {
        str(task.id): {
            "task_spec": task.task_spec.name,
            "state": task.state
        }
        for task in workflow.get_tasks()
    }

    # Extract minimal subprocess info
    subprocesses = {}
    for name, subprocess in workflow.subprocesses.items():
        # name might be a UUID, convert to string for JSON serialization
        subprocesses[str(name)] = {
            "spec": subprocess.spec.name,
            "tasks": {
                str(task.id): {
                    "task_spec": task.task_spec.name,
                    "state": task.state
                }
                for task in subprocess.get_tasks()
            }
        }

    return {
        "tasks": tasks,
        "subprocesses": subprocesses
    }

def build_response(workflow, e, compress_state=False, lazy_loads_result=None):
    """Build response with workflow state.

    Args:
        workflow: The workflow instance
        e: Exception if error occurred, None otherwise
        compress_state: If True, compress state with gzip
        lazy_loads_result: Optional pre-computed lazy_loads list. If None, will be computed.

    Returns:
        JSON string with response data
    """
    completed = workflow.completed

    if e is None:
        response = { "status": "ok", "completed": completed }
    else:
        response = {
            "status": "error",
            "message": f"{e}",
            "error_tasks": get_tasks(workflow, TaskFilter(TaskState.ERROR)),
        }

        if isinstance(e, WorkflowTaskException):
            response["line_number"] = e.line_number
            response["offset"] = e.offset
            response["error_line"] = e.error_line

    if completed:
        response["result"] = workflow.data
    else:
        response["pending_tasks"] = get_tasks(
            workflow,
            TaskFilter(TaskState.STARTED | TaskState.READY | TaskState.WAITING),
        )
        response["lazy_loads"] = lazy_loads_result if lazy_loads_result is not None else lazy_loads(workflow)

    # Use minimal state (only task_spec and state fields for diagram coloring)
    # Full state is no longer needed since workflow is cached in Python
    response["state"] = get_minimal_state(workflow)

    return json.dumps(response)

def clear_workflow_cache(session_id=None):
    """Clear cached workflows.

    Args:
        session_id: Optional session ID. If provided, only clear that session.
                   If None, clear all cached workflows.

    Returns:
        Number of entries cleared
    """
    global _workflow_cache
    if session_id:
        if session_id in _workflow_cache:
            del _workflow_cache[session_id]
            return 1
        return 0
    else:
        count = len(_workflow_cache)
        _workflow_cache.clear()
        return count
