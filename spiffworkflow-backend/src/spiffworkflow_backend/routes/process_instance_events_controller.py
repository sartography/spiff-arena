


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

    log_query = (
        ProcessInstanceEventModel.query.filter_by(process_instance_id=process_instance.id)
        .outerjoin(TaskModel, TaskModel.guid == ProcessInstanceEventModel.task_guid)
        .outerjoin(TaskDefinitionModel, TaskDefinitionModel.id == TaskModel.task_definition_id)
        .outerjoin(
            BpmnProcessDefinitionModel,
            BpmnProcessDefinitionModel.id == TaskDefinitionModel.bpmn_process_definition_id,
        )
    )
    if not detailed:
        log_query = log_query.filter(
            and_(
                TaskModel.state.in_(["COMPLETED"]),  # type: ignore
                TaskDefinitionModel.typename.in_(["IntermediateThrowEvent"]),  # type: ignore
            )
        )

    logs = (
        log_query.order_by(
            ProcessInstanceEventModel.timestamp.desc(), ProcessInstanceEventModel.id.desc()  # type: ignore
        )
        .outerjoin(UserModel, UserModel.id == ProcessInstanceEventModel.user_id)
        .add_columns(
            TaskModel.guid.label("spiff_task_guid"),  # type: ignore
            UserModel.username,
            BpmnProcessDefinitionModel.bpmn_identifier.label("bpmn_process_definition_identifier"),  # type: ignore
            BpmnProcessDefinitionModel.bpmn_name.label("bpmn_process_definition_name"),  # type: ignore
            TaskDefinitionModel.bpmn_identifier.label("task_definition_identifier"),  # type: ignore
            TaskDefinitionModel.bpmn_name.label("task_definition_name"),  # type: ignore
            TaskDefinitionModel.typename.label("bpmn_task_type"),  # type: ignore
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
