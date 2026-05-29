#!/usr/bin/env python

from __future__ import annotations

import argparse
import json
from hashlib import sha256

from spiffworkflow_backend import create_app
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.bpmn_process_definition_relationship import BpmnProcessDefinitionRelationshipModel
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel
from spiffworkflow_backend.services.bpmn_process_service import BpmnProcessService
from spiffworkflow_backend.services.process_model_service import ProcessModelService


def single_process_hash(process_bpmn_properties: dict) -> str:
    return sha256(json.dumps(process_bpmn_properties, sort_keys=True).encode("utf8")).hexdigest()


def full_process_model_hash(full_bpmn_spec_dict: dict) -> str:
    return sha256(json.dumps(full_bpmn_spec_dict, sort_keys=True).encode("utf8")).hexdigest()


def audit_definition(
    process_model_identifier: str, expected_definition: dict, persisted_definition: BpmnProcessDefinitionModel
) -> list[dict]:
    expected_task_definition_count = len(expected_definition["task_specs"])
    actual_task_definition_count = TaskDefinitionModel.query.filter_by(bpmn_process_definition_id=persisted_definition.id).count()

    if expected_task_definition_count == actual_task_definition_count:
        return []

    return [
        {
            "process_model_id": process_model_identifier,
            "issue": "task_definition_count_mismatch",
            "bpmn_identifier": expected_definition["name"],
            "persisted_bpmn_process_definition_id": persisted_definition.id,
            "expected_task_definition_count": expected_task_definition_count,
            "actual_task_definition_count": actual_task_definition_count,
        }
    ]


def audit_process_model(process_model_identifier: str) -> list[dict]:
    (
        bpmn_process_spec,
        subprocesses,
    ) = BpmnProcessService.get_process_model_and_subprocesses(process_model_identifier)
    bpmn_process_instance = BpmnProcessService.get_bpmn_process_instance_from_workflow_spec(bpmn_process_spec, subprocesses)
    serialized_process = BpmnProcessService.serialize(bpmn_process_instance)

    process_issues = []
    parent_spec = serialized_process["spec"]
    full_hash_input = {
        key: serialized_process[key]
        for key in BpmnProcessDefinitionModel.keys_for_full_process_model_hash()
        if key in serialized_process
    }
    parent_definition = BpmnProcessDefinitionModel.query.filter_by(
        full_process_model_hash=full_process_model_hash(full_hash_input)
    ).first()
    if parent_definition is None:
        return process_issues

    process_issues.extend(
        audit_definition(
            process_model_identifier=process_model_identifier,
            expected_definition=parent_spec,
            persisted_definition=parent_definition,
        )
    )

    expected_subprocess_hashes = []
    for subprocess_spec in serialized_process["subprocess_specs"].values():
        expected_hash = single_process_hash(subprocess_spec)
        expected_subprocess_hashes.append(expected_hash)
        persisted_subprocess = BpmnProcessDefinitionModel.query.filter_by(single_process_hash=expected_hash).first()
        if persisted_subprocess is None:
            continue
        process_issues.extend(
            audit_definition(
                process_model_identifier=process_model_identifier,
                expected_definition=subprocess_spec,
                persisted_definition=persisted_subprocess,
            )
        )

    actual_subprocess_hashes = sorted(
        child.single_process_hash
        for child in BpmnProcessDefinitionModel.query.join(
            BpmnProcessDefinitionRelationshipModel,
            BpmnProcessDefinitionModel.id == BpmnProcessDefinitionRelationshipModel.bpmn_process_definition_child_id,
        )
        .filter(BpmnProcessDefinitionRelationshipModel.bpmn_process_definition_parent_id == parent_definition.id)
        .all()
    )
    if sorted(expected_subprocess_hashes) != actual_subprocess_hashes:
        process_issues.append(
            {
                "process_model_id": process_model_identifier,
                "issue": "subprocess_relationship_mismatch",
                "bpmn_identifier": parent_spec["name"],
                "expected_subprocess_hashes": sorted(expected_subprocess_hashes),
                "actual_subprocess_hashes": actual_subprocess_hashes,
            }
        )

    return process_issues


def audit_all_process_models(include_parse_failures: bool = False) -> list[dict]:
    issues = []
    process_models = ProcessModelService.get_process_models(recursive=True)
    for process_model in process_models:
        try:
            issues.extend(audit_process_model(process_model.id))
        except ApiError as exception:
            if include_parse_failures:
                issues.append(
                    {
                        "process_model_id": process_model.id,
                        "issue": "process_model_parse_failed",
                        "error": exception.message,
                        "error_code": exception.error_code,
                    }
                )
            continue
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--include-parse-failures", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = create_app()
    with app.app.app_context():
        issues = audit_all_process_models(include_parse_failures=args.include_parse_failures)

    if args.json_output:
        print(json.dumps({"issues": issues, "ok": len(issues) == 0}, indent=2, sort_keys=True))
        return 0 if not issues else 1

    if issues:
        print(json.dumps(issues, indent=2, sort_keys=True))
        return 1

    print("No process definition integrity issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
