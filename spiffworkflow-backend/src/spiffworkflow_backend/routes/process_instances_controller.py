"""APIs for dealing with process groups, process models, and process instances."""
import json
from typing import Any
from typing import Dict
from typing import Optional

import flask.wrappers
from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response
from flask import request
from flask.wrappers import Response
from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db
from SpiffWorkflow.task import TaskState  # type: ignore
from sqlalchemy import and_
from sqlalchemy import or_

from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceApiSchema
from spiffworkflow_backend.models.process_instance import (
    ProcessInstanceCannotBeDeletedError,
)
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModelSchema
from spiffworkflow_backend.models.process_instance_metadata import (
    ProcessInstanceMetadataModel,
)
from spiffworkflow_backend.models.process_instance_report import (
    ProcessInstanceReportModel,
)
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.spec_reference import SpecReferenceCache
from spiffworkflow_backend.models.spec_reference import SpecReferenceNotFoundError
from spiffworkflow_backend.models.spiff_logging import SpiffLoggingModel
from spiffworkflow_backend.models.spiff_step_details import SpiffStepDetailsModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.routes.process_api_blueprint import (
    _find_process_instance_by_id_or_raise,
)
from spiffworkflow_backend.routes.process_api_blueprint import _get_process_model
from spiffworkflow_backend.routes.process_api_blueprint import (
    _un_modify_modified_process_model_id,
)
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.error_handling_service import ErrorHandlingService
from spiffworkflow_backend.services.git_service import GitCommandError
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_instance_report_service import (
    ProcessInstanceReportFilter,
)
from spiffworkflow_backend.services.process_instance_report_service import (
    ProcessInstanceReportService,
)
from spiffworkflow_backend.services.process_instance_service import (
    ProcessInstanceService,
)
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService


def process_instance_create(
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    """Create_process_instance."""
    process_model_identifier = _un_modify_modified_process_model_id(
        modified_process_model_identifier
    )
    process_instance = (
        ProcessInstanceService.create_process_instance_from_process_model_identifier(
            process_model_identifier, g.user
        )
    )
    return Response(
        json.dumps(ProcessInstanceModelSchema().dump(process_instance)),
        status=201,
        mimetype="application/json",
    )


def process_instance_run(
    modified_process_model_identifier: str,
    process_instance_id: int,
    do_engine_steps: bool = True,
) -> flask.wrappers.Response:
    """Process_instance_run."""
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    if process_instance.status != "not_started":
        raise ApiError(
            error_code="process_instance_not_runnable",
            message=(
                f"Process Instance ({process_instance.id}) is currently running or has"
                " already run."
            ),
            status_code=400,
        )

    processor = ProcessInstanceProcessor(process_instance)

    if do_engine_steps:
        try:
            processor.do_engine_steps(save=True)
        except ApiError as e:
            ErrorHandlingService().handle_error(processor, e)
            raise e
        except Exception as e:
            ErrorHandlingService().handle_error(processor, e)
            task = processor.bpmn_process_instance.last_task
            raise ApiError.from_task(
                error_code="unknown_exception",
                message=f"An unknown error occurred. Original error: {e}",
                status_code=400,
                task=task,
            ) from e

        if not current_app.config["RUN_BACKGROUND_SCHEDULER"]:
            MessageService.process_message_instances()

    process_instance_api = ProcessInstanceService.processor_to_process_instance_api(
        processor
    )
    process_instance_data = processor.get_data()
    process_instance_metadata = ProcessInstanceApiSchema().dump(process_instance_api)
    process_instance_metadata["data"] = process_instance_data
    return Response(
        json.dumps(process_instance_metadata), status=200, mimetype="application/json"
    )


def process_instance_terminate(
    process_instance_id: int,
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    """Process_instance_run."""
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    processor = ProcessInstanceProcessor(process_instance)
    processor.terminate()
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_suspend(
    process_instance_id: int,
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    """Process_instance_suspend."""
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    processor = ProcessInstanceProcessor(process_instance)
    processor.suspend()
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_resume(
    process_instance_id: int,
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    """Process_instance_resume."""
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    processor = ProcessInstanceProcessor(process_instance)
    processor.resume()
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_log_list(
    modified_process_model_identifier: str,
    process_instance_id: int,
    page: int = 1,
    per_page: int = 100,
    detailed: bool = False,
) -> flask.wrappers.Response:
    """Process_instance_log_list."""
    # to make sure the process instance exists
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)

    log_query = SpiffLoggingModel.query.filter(
        SpiffLoggingModel.process_instance_id == process_instance.id
    )
    if not detailed:
        log_query = log_query.filter(SpiffLoggingModel.message.in_(["State change to COMPLETED"]))  # type: ignore

    logs = (
        log_query.order_by(SpiffLoggingModel.timestamp.desc())  # type: ignore
        .join(
            UserModel, UserModel.id == SpiffLoggingModel.current_user_id, isouter=True
        )  # isouter since if we don't have a user, we still want the log
        .add_columns(
            UserModel.username,
        )
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    response_json = {
        "results": logs.items,
        "pagination": {
            "count": len(logs.items),
            "total": logs.total,
            "pages": logs.pages,
        },
    }

    return make_response(jsonify(response_json), 200)


def process_instance_list_for_me(
    process_model_identifier: Optional[str] = None,
    page: int = 1,
    per_page: int = 100,
    start_from: Optional[int] = None,
    start_to: Optional[int] = None,
    end_from: Optional[int] = None,
    end_to: Optional[int] = None,
    process_status: Optional[str] = None,
    user_filter: Optional[bool] = False,
    report_identifier: Optional[str] = None,
    report_id: Optional[int] = None,
    user_group_identifier: Optional[str] = None,
) -> flask.wrappers.Response:
    """Process_instance_list_for_me."""
    return process_instance_list(
        process_model_identifier=process_model_identifier,
        page=page,
        per_page=per_page,
        start_from=start_from,
        start_to=start_to,
        end_from=end_from,
        end_to=end_to,
        process_status=process_status,
        user_filter=user_filter,
        report_identifier=report_identifier,
        report_id=report_id,
        user_group_identifier=user_group_identifier,
        with_relation_to_me=True,
    )


def process_instance_list(
    process_model_identifier: Optional[str] = None,
    page: int = 1,
    per_page: int = 100,
    start_from: Optional[int] = None,
    start_to: Optional[int] = None,
    end_from: Optional[int] = None,
    end_to: Optional[int] = None,
    process_status: Optional[str] = None,
    with_relation_to_me: Optional[bool] = None,
    user_filter: Optional[bool] = False,
    report_identifier: Optional[str] = None,
    report_id: Optional[int] = None,
    user_group_identifier: Optional[str] = None,
) -> flask.wrappers.Response:
    """Process_instance_list."""
    process_instance_report = ProcessInstanceReportService.report_with_identifier(
        g.user, report_id, report_identifier
    )

    if user_filter:
        report_filter = ProcessInstanceReportFilter(
            process_model_identifier=process_model_identifier,
            user_group_identifier=user_group_identifier,
            start_from=start_from,
            start_to=start_to,
            end_from=end_from,
            end_to=end_to,
            with_relation_to_me=with_relation_to_me,
            process_status=process_status.split(",") if process_status else None,
        )
    else:
        report_filter = (
            ProcessInstanceReportService.filter_from_metadata_with_overrides(
                process_instance_report=process_instance_report,
                process_model_identifier=process_model_identifier,
                user_group_identifier=user_group_identifier,
                start_from=start_from,
                start_to=start_to,
                end_from=end_from,
                end_to=end_to,
                process_status=process_status,
                with_relation_to_me=with_relation_to_me,
            )
        )

    response_json = ProcessInstanceReportService.run_process_instance_report(
        report_filter=report_filter,
        process_instance_report=process_instance_report,
        page=page,
        per_page=per_page,
        user=g.user,
    )

    return make_response(jsonify(response_json), 200)


def process_instance_report_column_list() -> flask.wrappers.Response:
    """Process_instance_report_column_list."""
    table_columns = ProcessInstanceReportService.builtin_column_options()
    columns_for_metadata = (
        db.session.query(ProcessInstanceMetadataModel.key)
        .order_by(ProcessInstanceMetadataModel.key)
        .distinct()  # type: ignore
        .all()
    )
    columns_for_metadata_strings = [
        {"Header": i[0], "accessor": i[0], "filterable": True}
        for i in columns_for_metadata
    ]
    return make_response(jsonify(table_columns + columns_for_metadata_strings), 200)


def process_instance_show_for_me(
    modified_process_model_identifier: str,
    process_instance_id: int,
    process_identifier: Optional[str] = None,
) -> flask.wrappers.Response:
    """Process_instance_show_for_me."""
    process_instance = _find_process_instance_for_me_or_raise(process_instance_id)
    return _get_process_instance(
        process_instance=process_instance,
        modified_process_model_identifier=modified_process_model_identifier,
        process_identifier=process_identifier,
    )


def process_instance_show(
    modified_process_model_identifier: str,
    process_instance_id: int,
    process_identifier: Optional[str] = None,
) -> flask.wrappers.Response:
    """Create_process_instance."""
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    return _get_process_instance(
        process_instance=process_instance,
        modified_process_model_identifier=modified_process_model_identifier,
        process_identifier=process_identifier,
    )


def process_instance_delete(
    process_instance_id: int, modified_process_model_identifier: str
) -> flask.wrappers.Response:
    """Create_process_instance."""
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)

    if not process_instance.has_terminal_status():
        raise ProcessInstanceCannotBeDeletedError(
            f"Process instance ({process_instance.id}) cannot be deleted since it does"
            f" not have a terminal status. Current status is {process_instance.status}."
        )

    # (Pdb) db.session.delete
    # <bound method delete of <sqlalchemy.orm.scoping.scoped_session object at 0x103eaab30>>
    db.session.query(SpiffLoggingModel).filter_by(
        process_instance_id=process_instance.id
    ).delete()
    db.session.query(SpiffStepDetailsModel).filter_by(
        process_instance_id=process_instance.id
    ).delete()
    db.session.delete(process_instance)
    db.session.commit()
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_report_list(
    page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    """Process_instance_report_list."""
    process_instance_reports = ProcessInstanceReportModel.query.filter_by(
        created_by_id=g.user.id,
    ).all()

    return make_response(jsonify(process_instance_reports), 200)


def process_instance_report_create(body: Dict[str, Any]) -> flask.wrappers.Response:
    """Process_instance_report_create."""
    process_instance_report = ProcessInstanceReportModel.create_report(
        identifier=body["identifier"],
        user=g.user,
        report_metadata=body["report_metadata"],
    )

    return make_response(jsonify(process_instance_report), 201)


def process_instance_report_update(
    report_id: int,
    body: Dict[str, Any],
) -> flask.wrappers.Response:
    """Process_instance_report_update."""
    process_instance_report = ProcessInstanceReportModel.query.filter_by(
        id=report_id,
        created_by_id=g.user.id,
    ).first()
    if process_instance_report is None:
        raise ApiError(
            error_code="unknown_process_instance_report",
            message="Unknown process instance report",
            status_code=404,
        )

    process_instance_report.report_metadata = body["report_metadata"]
    db.session.commit()

    return make_response(jsonify(process_instance_report), 201)


def process_instance_report_delete(
    report_id: int,
) -> flask.wrappers.Response:
    """Process_instance_report_delete."""
    process_instance_report = ProcessInstanceReportModel.query.filter_by(
        id=report_id,
        created_by_id=g.user.id,
    ).first()
    if process_instance_report is None:
        raise ApiError(
            error_code="unknown_process_instance_report",
            message="Unknown process instance report",
            status_code=404,
        )

    db.session.delete(process_instance_report)
    db.session.commit()

    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_report_show(
    report_id: int,
    page: int = 1,
    per_page: int = 100,
) -> flask.wrappers.Response:
    """Process_instance_report_show."""
    process_instances = ProcessInstanceModel.query.order_by(
        ProcessInstanceModel.start_in_seconds.desc(), ProcessInstanceModel.id.desc()  # type: ignore
    ).paginate(page=page, per_page=per_page, error_out=False)

    process_instance_report = ProcessInstanceReportModel.query.filter_by(
        id=report_id,
        created_by_id=g.user.id,
    ).first()
    if process_instance_report is None:
        raise ApiError(
            error_code="unknown_process_instance_report",
            message="Unknown process instance report",
            status_code=404,
        )

    substitution_variables = request.args.to_dict()
    result_dict = process_instance_report.generate_report(
        process_instances.items, substitution_variables
    )

    # update this if we go back to a database query instead of filtering in memory
    result_dict["pagination"] = {
        "count": len(result_dict["results"]),
        "total": len(result_dict["results"]),
        "pages": 1,
    }

    return Response(json.dumps(result_dict), status=200, mimetype="application/json")


def process_instance_task_list_without_task_data_for_me(
    modified_process_model_identifier: str,
    process_instance_id: int,
    all_tasks: bool = False,
    spiff_step: int = 0,
) -> flask.wrappers.Response:
    """Process_instance_task_list_without_task_data_for_me."""
    process_instance = _find_process_instance_for_me_or_raise(process_instance_id)
    return process_instance_task_list(
        modified_process_model_identifier,
        process_instance,
        all_tasks,
        spiff_step,
        get_task_data=False,
    )


def process_instance_task_list_without_task_data(
    modified_process_model_identifier: str,
    process_instance_id: int,
    all_tasks: bool = False,
    spiff_step: int = 0,
) -> flask.wrappers.Response:
    """Process_instance_task_list_without_task_data."""
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    return process_instance_task_list(
        modified_process_model_identifier,
        process_instance,
        all_tasks,
        spiff_step,
        get_task_data=False,
    )


def process_instance_task_list_with_task_data(
    modified_process_model_identifier: str,
    process_instance_id: int,
    all_tasks: bool = False,
    spiff_step: int = 0,
) -> flask.wrappers.Response:
    """Process_instance_task_list_with_task_data."""
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    return process_instance_task_list(
        modified_process_model_identifier,
        process_instance,
        all_tasks,
        spiff_step,
        get_task_data=True,
    )


def process_instance_task_list(
    _modified_process_model_identifier: str,
    process_instance: ProcessInstanceModel,
    all_tasks: bool = False,
    spiff_step: int = 0,
    get_task_data: bool = False,
) -> flask.wrappers.Response:
    """Process_instance_task_list."""
    if spiff_step > 0:
        step_detail = (
            db.session.query(SpiffStepDetailsModel)
            .filter(
                SpiffStepDetailsModel.process_instance_id == process_instance.id,
                SpiffStepDetailsModel.spiff_step == spiff_step,
            )
            .first()
        )
        if step_detail is not None and process_instance.bpmn_json is not None:
            bpmn_json = json.loads(process_instance.bpmn_json)
            bpmn_json["tasks"] = step_detail.task_json["tasks"]
            bpmn_json["subprocesses"] = step_detail.task_json["subprocesses"]
            process_instance.bpmn_json = json.dumps(bpmn_json)

    processor = ProcessInstanceProcessor(process_instance)

    spiff_tasks = None
    if all_tasks:
        spiff_tasks = processor.bpmn_process_instance.get_tasks(TaskState.ANY_MASK)
    else:
        spiff_tasks = processor.get_all_user_tasks()

    subprocesses_by_child_task_ids = processor.get_subprocesses_by_child_task_ids()
    processor.get_highest_level_subprocesses_by_child_task_ids(
        subprocesses_by_child_task_ids
    )

    tasks = []
    for spiff_task in spiff_tasks:
        calling_subprocess_task_id = subprocesses_by_child_task_ids.get(
            str(spiff_task.id), None
        )
        task = ProcessInstanceService.spiff_task_to_api_task(
            processor, spiff_task, calling_subprocess_task_id=calling_subprocess_task_id
        )
        if get_task_data:
            task.data = spiff_task.data
        tasks.append(task)

    return make_response(jsonify(tasks), 200)


def process_instance_reset(
    process_instance_id: int,
    modified_process_model_identifier: str,
    spiff_step: int = 0,
) -> flask.wrappers.Response:
    """Reset a process instance to a particular step."""
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    processor = ProcessInstanceProcessor(process_instance)
    processor.reset_process(spiff_step)
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_find_by_id(
    process_instance_id: int,
) -> flask.wrappers.Response:
    """Process_instance_find_by_id."""
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    modified_process_model_identifier = (
        ProcessModelInfo.modify_process_identifier_for_path_param(
            process_instance.process_model_identifier
        )
    )
    process_instance_uri = (
        f"/process-instances/{modified_process_model_identifier}/{process_instance.id}"
    )
    has_permission = AuthorizationService.user_has_permission(
        user=g.user,
        permission="read",
        target_uri=process_instance_uri,
    )

    uri_type = None
    if not has_permission:
        process_instance = _find_process_instance_for_me_or_raise(process_instance_id)
        uri_type = "for-me"

    response_json = {
        "process_instance": process_instance,
        "uri_type": uri_type,
    }
    return make_response(jsonify(response_json), 200)


def _get_process_instance(
    modified_process_model_identifier: str,
    process_instance: ProcessInstanceModel,
    process_identifier: Optional[str] = None,
) -> flask.wrappers.Response:
    """_get_process_instance."""
    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    try:
        current_version_control_revision = GitService.get_current_revision()
    except GitCommandError:
        current_version_control_revision = ""

    process_model_with_diagram = None
    name_of_file_with_diagram = None
    if process_identifier:
        spec_reference = SpecReferenceCache.query.filter_by(
            identifier=process_identifier, type="process"
        ).first()
        if spec_reference is None:
            raise SpecReferenceNotFoundError(
                "Could not find given process identifier in the cache:"
                f" {process_identifier}"
            )

        process_model_with_diagram = ProcessModelService.get_process_model(
            spec_reference.process_model_id
        )
        name_of_file_with_diagram = spec_reference.file_name
    else:
        process_model_with_diagram = _get_process_model(process_model_identifier)
        if process_model_with_diagram.primary_file_name:
            name_of_file_with_diagram = process_model_with_diagram.primary_file_name

    if process_model_with_diagram and name_of_file_with_diagram:
        if (
            process_instance.bpmn_version_control_identifier
            == current_version_control_revision
        ):
            bpmn_xml_file_contents = SpecFileService.get_data(
                process_model_with_diagram, name_of_file_with_diagram
            ).decode("utf-8")
        else:
            bpmn_xml_file_contents = GitService.get_instance_file_contents_for_revision(
                process_model_with_diagram,
                process_instance.bpmn_version_control_identifier,
                file_name=name_of_file_with_diagram,
            )
        process_instance.bpmn_xml_file_contents = bpmn_xml_file_contents

    return make_response(jsonify(process_instance), 200)


def _find_process_instance_for_me_or_raise(
    process_instance_id: int,
) -> ProcessInstanceModel:
    """_find_process_instance_for_me_or_raise."""
    process_instance: ProcessInstanceModel = (
        ProcessInstanceModel.query.filter_by(id=process_instance_id)
        .outerjoin(HumanTaskModel)
        .outerjoin(
            HumanTaskUserModel,
            and_(
                HumanTaskModel.id == HumanTaskUserModel.human_task_id,
                HumanTaskUserModel.user_id == g.user.id,
            ),
        )
        .filter(
            or_(
                HumanTaskUserModel.id.is_not(None),
                ProcessInstanceModel.process_initiator_id == g.user.id,
            )
        )
        .first()
    )

    if process_instance is None:
        raise (
            ApiError(
                error_code="process_instance_cannot_be_found",
                message=(
                    f"Process instance with id {process_instance_id} cannot be found"
                    " that is associated with you."
                ),
                status_code=400,
            )
        )

    return process_instance
