"""APIs for dealing with process groups, process models, and process instances."""

import json
import secrets
import string

import flask.wrappers
from flask import current_app
from flask import jsonify
from flask import make_response
from flask.wrappers import Response
from lxml import etree  # type: ignore
from lxml.builder import ElementMaker  # type: ignore

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.routes.process_api_blueprint import _get_process_model
from spiffworkflow_backend.routes.process_api_blueprint import _get_required_parameter_or_raise
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.script_unit_test_runner import ScriptUnitTestRunner
from spiffworkflow_backend.services.spec_file_service import SpecFileService


def script_unit_test_create(modified_process_model_identifier: str, body: dict[str, str | bool | int]) -> flask.wrappers.Response:
    bpmn_task_identifier = _get_required_parameter_or_raise("bpmn_task_identifier", body)
    input_json = _get_required_parameter_or_raise("input_json", body)
    expected_output_json = _get_required_parameter_or_raise("expected_output_json", body)

    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    process_model = _get_process_model(process_model_identifier)
    file = FileSystemService.get_files(process_model, process_model.primary_file_name)[0]
    if file is None:
        raise ApiError(
            error_code="cannot_find_file",
            message=f"Could not find the primary bpmn file for process_model: {process_model.id}",
            status_code=404,
        )

    # TODO: move this to an xml service or something
    file_contents = SpecFileService.get_data(process_model, file.name)
    bpmn_etree_element = SpecFileService.get_etree_from_xml_bytes(file_contents)

    nsmap = bpmn_etree_element.nsmap
    spiff_element_maker = ElementMaker(namespace="http://spiffworkflow.org/bpmn/schema/1.0/core", nsmap=nsmap)

    script_task_elements = bpmn_etree_element.xpath(
        f"//bpmn:scriptTask[@id='{bpmn_task_identifier}']",
        namespaces={"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"},
    )
    if len(script_task_elements) == 0:
        raise ApiError(
            error_code="missing_script_task",
            message=f"Cannot find a script task with id: {bpmn_task_identifier}",
            status_code=404,
        )
    script_task_element = script_task_elements[0]

    extension_elements = None
    extension_elements_array = script_task_element.xpath(
        ".//bpmn:extensionElements",
        namespaces={"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"},
    )
    if len(extension_elements_array) == 0:
        bpmn_element_maker = ElementMaker(namespace="http://www.omg.org/spec/BPMN/20100524/MODEL", nsmap=nsmap)
        extension_elements = bpmn_element_maker("extensionElements")
        script_task_element.append(extension_elements)
    else:
        extension_elements = extension_elements_array[0]

    unit_test_elements = None
    unit_test_elements_array = extension_elements.xpath(
        "//spiffworkflow:unitTests",
        namespaces={"spiffworkflow": "http://spiffworkflow.org/bpmn/schema/1.0/core"},
    )
    if len(unit_test_elements_array) == 0:
        unit_test_elements = spiff_element_maker("unitTests")
        extension_elements.append(unit_test_elements)
    else:
        unit_test_elements = unit_test_elements_array[0]

    fuzz = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(7))  # noqa: S311
    unit_test_id = f"unit_test_{fuzz}"

    input_json_element = spiff_element_maker("inputJson", json.dumps(input_json))
    expected_output_json_element = spiff_element_maker("expectedOutputJson", json.dumps(expected_output_json))
    unit_test_element = spiff_element_maker("unitTest", id=unit_test_id)
    unit_test_element.append(input_json_element)
    unit_test_element.append(expected_output_json_element)
    unit_test_elements.append(unit_test_element)
    SpecFileService.update_file(process_model, file.name, etree.tostring(bpmn_etree_element))

    return Response(json.dumps({"ok": True}), status=202, mimetype="application/json")


def script_unit_test_run(modified_process_model_identifier: str, body: dict[str, str | bool | int]) -> flask.wrappers.Response:
    # FIXME: We should probably clear this somewhere else but this works
    current_app.config["THREAD_LOCAL_DATA"].process_instance_id = None

    python_script = _get_required_parameter_or_raise("python_script", body)
    input_json = _get_required_parameter_or_raise("input_json", body)
    expected_output_json = _get_required_parameter_or_raise("expected_output_json", body)

    result = ScriptUnitTestRunner.run_with_script_and_pre_post_contexts(python_script, input_json, expected_output_json)
    return make_response(jsonify(result), 200)
