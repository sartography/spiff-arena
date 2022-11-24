"""APIs for dealing with process groups, process models, and process instances."""
from typing import Union

from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.wrappers import Response

from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_instance_service import (
    ProcessInstanceService,
)
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.user_service import UserService

admin_blueprint = Blueprint(
    "admin", __name__, template_folder="templates", static_folder="static"
)

ALLOWED_BPMN_EXTENSIONS = {"bpmn", "dmn"}


@admin_blueprint.route("/process-groups", methods=["GET"])
def process_group_list() -> str:
    """Process_group_list."""
    process_groups = ProcessModelService.get_process_groups()
    return render_template("process_group_list.html", process_groups=process_groups)


@admin_blueprint.route("/process-groups/<process_group_id>", methods=["GET"])
def process_group_show(process_group_id: str) -> str:
    """Show_process_group."""
    process_group = ProcessModelService.get_process_group(process_group_id)
    return render_template("process_group_show.html", process_group=process_group)


@admin_blueprint.route("/process-models/<process_model_id>", methods=["GET"])
def process_model_show(process_model_id: str) -> Union[str, Response]:
    """Show_process_model."""
    process_model = ProcessModelService.get_process_model(process_model_id)
    files = SpecFileService.get_files(process_model, extension_filter="bpmn")
    current_file_name = process_model.primary_file_name
    if current_file_name is None:
        flash("No primary_file_name", "error")
        return redirect(url_for("admin.process_group_list"))
    bpmn_xml = SpecFileService.get_data(process_model, current_file_name)
    return render_template(
        "process_model_show.html",
        process_model=process_model,
        bpmn_xml=bpmn_xml,
        files=files,
        current_file_name=current_file_name,
    )


@admin_blueprint.route(
    "/process-models/<process_model_id>/<file_name>", methods=["GET"]
)
def process_model_show_file(process_model_id: str, file_name: str) -> str:
    """Process_model_show_file."""
    process_model = ProcessModelService.get_process_model(process_model_id)
    bpmn_xml = SpecFileService.get_data(process_model, file_name)
    files = SpecFileService.get_files(process_model, extension_filter="bpmn")
    return render_template(
        "process_model_show.html",
        process_model=process_model,
        bpmn_xml=bpmn_xml,
        files=files,
        current_file_name=file_name,
    )


@admin_blueprint.route(
    "/process-models/<process_model_id>/upload-file", methods=["POST"]
)
def process_model_upload_file(process_model_id: str) -> Response:
    """Process_model_upload_file."""
    process_model_service = ProcessModelService()
    process_model = process_model_service.get_process_model(process_model_id)

    if "file" not in request.files:
        flash("No file part", "error")
    request_file = request.files["file"]
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if request_file.filename == "" or request_file.filename is None:
        flash("No selected file", "error")
    else:
        if request_file and _allowed_file(request_file.filename):
            if request_file.filename is not None:
                SpecFileService.add_file(
                    process_model, request_file.filename, request_file.stream.read()
                )
                process_model_service.save_process_model(process_model)

    return redirect(
        url_for("admin.process_model_show", process_model_id=process_model.id)
    )


@admin_blueprint.route(
    "/process_models/<process_model_id>/edit/<file_name>", methods=["GET"]
)
def process_model_edit(process_model_id: str, file_name: str) -> str:
    """Edit_bpmn."""
    process_model = ProcessModelService.get_process_model(process_model_id)
    bpmn_xml = SpecFileService.get_data(process_model, file_name)

    return render_template(
        "process_model_edit.html",
        bpmn_xml=bpmn_xml.decode("utf-8"),
        process_model=process_model,
        file_name=file_name,
    )


@admin_blueprint.route(
    "/process-models/<process_model_id>/save/<file_name>", methods=["POST"]
)
def process_model_save(process_model_id: str, file_name: str) -> Union[str, Response]:
    """Process_model_save."""
    process_model = ProcessModelService.get_process_model(process_model_id)
    SpecFileService.update_file(process_model, file_name, request.get_data())
    if process_model.primary_file_name is None:
        flash("No primary_file_name", "error")
        return redirect(url_for("admin.process_group_list"))
    bpmn_xml = SpecFileService.get_data(process_model, process_model.primary_file_name)
    return render_template(
        "process_model_edit.html",
        bpmn_xml=bpmn_xml.decode("utf-8"),
        process_model=process_model,
        file_name=file_name,
    )


@admin_blueprint.route("/process-models/<process_model_id>/run", methods=["GET"])
def process_model_run(process_model_id: str) -> Union[str, Response]:
    """Process_model_run."""
    user = UserService.create_user("internal", "Mr. Test", username="Mr. Test")
    process_instance = (
        ProcessInstanceService.create_process_instance_from_process_model_identifier(
            process_model_id, user
        )
    )
    processor = ProcessInstanceProcessor(process_instance)
    processor.do_engine_steps()
    result = processor.get_data()

    process_model = ProcessModelService.get_process_model(process_model_id)
    files = SpecFileService.get_files(process_model, extension_filter="bpmn")
    current_file_name = process_model.primary_file_name
    if current_file_name is None:
        flash("No primary_file_name", "error")
        return redirect(url_for("admin.process_group_list"))
    bpmn_xml = SpecFileService.get_data(process_model, current_file_name)

    return render_template(
        "process_model_show.html",
        process_model=process_model,
        bpmn_xml=bpmn_xml,
        result=result,
        files=files,
        current_file_name=current_file_name,
    )


# def _find_or_create_user(username: str = "test_user1") -> Any:
#     """Find_or_create_user."""
#     user = UserModel.query.filter_by(username=username).first()
#     if user is None:
#         user = UserModel(username=username)
#         db.session.add(user)
#         db.session.commit()
#     return user


def _allowed_file(filename: str) -> bool:
    """_allowed_file."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_BPMN_EXTENSIONS
    )
