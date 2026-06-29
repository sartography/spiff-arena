from typing import Any

from flask.app import Flask

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.scripts.delete_process_instances_with_criteria import DeleteProcessInstancesWithCriteria


def add_process_instance(id: int, process_model_identifier: str, status: str, user: UserModel) -> ProcessInstanceModel:
    process_instance = ProcessInstanceModel(
        id=id,
        process_model_identifier=process_model_identifier,
        process_model_display_name=process_model_identifier,
        process_initiator_id=user.id,
        status=status,
        updated_at_in_seconds=1,
    )
    db.session.add(process_instance)
    return process_instance


def run_script(criteria: list[dict[str, Any]], **kwargs: Any) -> Any:
    return DeleteProcessInstancesWithCriteria().run(
        ScriptAttributesContext(
            task=None,
            environment_identifier="unit_testing",
            process_instance_id=1,
            process_model_identifier="cleanup/reaper",
        ),
        criteria,
        **kwargs,
    )


def test_delete_process_instances_with_criteria_returns_summary_and_honors_limit(
    app: Flask,
    with_db_and_bpmn_file_cleanup: None,
    with_super_admin_user: UserModel,
) -> None:
    assert app
    add_process_instance(1, "cleanup/model-a", "complete", with_super_admin_user)
    add_process_instance(2, "cleanup/model-a", "complete", with_super_admin_user)
    add_process_instance(3, "cleanup/model-a", "error", with_super_admin_user)
    add_process_instance(4, "cleanup/model-b", "complete", with_super_admin_user)
    add_process_instance(5, "cleanup/reaper-model", "complete", with_super_admin_user)
    db.session.commit()

    summary = run_script(
        [
            {"status": ["complete", "error"], "last_updated_delta": -1, "exclude_name_prefixes": ["cleanup/reaper"]},
            {"name": "cleanup/model-b", "status": ["complete"], "last_updated_delta": -1},
        ],
        limit=4,
        return_summary=True,
    )

    assert summary == {
        "total_deleted": 4,
        "limit": 4,
        "criteria_count": 2,
        "by_model_status": [
            {"process_model_identifier": "cleanup/model-a", "status": "complete", "deleted": 2},
            {"process_model_identifier": "cleanup/model-a", "status": "error", "deleted": 1},
            {"process_model_identifier": "cleanup/model-b", "status": "complete", "deleted": 1},
        ],
    }
    assert ProcessInstanceModel.query.filter_by(id=1).first() is None
    assert ProcessInstanceModel.query.filter_by(id=2).first() is None
    assert ProcessInstanceModel.query.filter_by(id=3).first() is None
    assert ProcessInstanceModel.query.filter_by(id=4).first() is None
    assert ProcessInstanceModel.query.filter_by(id=5).first() is not None


def test_delete_process_instances_with_criteria_keeps_integer_return_by_default(
    app: Flask,
    with_db_and_bpmn_file_cleanup: None,
    with_super_admin_user: UserModel,
) -> None:
    assert app
    add_process_instance(1, "cleanup/model-a", "complete", with_super_admin_user)
    add_process_instance(2, "cleanup/model-a", "complete", with_super_admin_user)
    db.session.commit()

    rows_affected = run_script(
        [{"name": "cleanup/model-a", "status": ["complete"], "last_updated_delta": -1}],
        limit=1,
    )

    assert rows_affected == 1
    assert ProcessInstanceModel.query.count() == 1


def test_delete_process_instances_with_criteria_escapes_excluded_name_prefixes(
    app: Flask,
    with_db_and_bpmn_file_cleanup: None,
    with_super_admin_user: UserModel,
) -> None:
    assert app
    add_process_instance(1, r"cleanup/%_literal/path", "complete", with_super_admin_user)
    add_process_instance(2, "cleanup/anythingliteral/path", "complete", with_super_admin_user)
    db.session.commit()

    rows_affected = run_script(
        [{"status": ["complete"], "last_updated_delta": -1, "exclude_name_prefixes": [r"cleanup/%_literal"]}],
        limit=10,
    )

    assert rows_affected == 1
    assert ProcessInstanceModel.query.filter_by(id=1).first() is not None
    assert ProcessInstanceModel.query.filter_by(id=2).first() is None
