import copy
import re
from collections.abc import Generator
from typing import Any

import sqlalchemy
from flask import current_app
from flask_sqlalchemy.query import Query
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy.orm import aliased
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.util import AliasedClass

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_metadata import ProcessInstanceMetadataModel
from spiffworkflow_backend.models.process_instance_report import FilterValue
from spiffworkflow_backend.models.process_instance_report import ProcessInstanceReportModel
from spiffworkflow_backend.models.process_instance_report import ReportMetadata
from spiffworkflow_backend.models.process_instance_report import ReportMetadataColumn
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user_group_assignment import UserGroupAssignmentModel
from spiffworkflow_backend.services.process_model_service import ProcessModelService


class ProcessInstanceReportNotFoundError(Exception):
    pass


class ProcessInstanceReportMetadataInvalidError(Exception):
    pass


class ProcessInstanceReportCannotBeRunError(Exception):
    pass


class ProcessInstanceReportService:
    @classmethod
    def system_metadata_map(cls, metadata_key: str) -> ReportMetadata | None:
        # TODO replace with system reports that are loaded on launch (or similar)
        terminal_status_values = ",".join(ProcessInstanceModel.terminal_statuses())
        non_terminal_status_values = ",".join(ProcessInstanceModel.non_terminal_statuses())
        active_status_values = ",".join(ProcessInstanceModel.active_statuses())
        default: ReportMetadata = {
            "columns": cls.builtin_column_options(),
            "filter_by": [],
            "order_by": ["-start_in_seconds", "-id"],
        }
        system_report_completed_instances_initiated_by_me: ReportMetadata = {
            "columns": [
                {"Header": "Id", "accessor": "id", "filterable": False},
                {
                    "Header": "Process",
                    "accessor": "process_model_display_name",
                    "filterable": False,
                },
                {"Header": "Start time", "accessor": "start_in_seconds", "filterable": False},
                {"Header": "End time", "accessor": "end_in_seconds", "filterable": False},
                {"Header": "Last milestone", "accessor": "last_milestone_bpmn_name", "filterable": False},
                {"Header": "Status", "accessor": "status", "filterable": False},
            ],
            "filter_by": [
                {"field_name": "initiated_by_me", "field_value": True, "operator": "equals"},
                {"field_name": "process_status", "field_value": terminal_status_values, "operator": "equals"},
            ],
            "order_by": ["-start_in_seconds", "-id"],
        }
        system_report_completed_instances_with_tasks_completed_by_me: ReportMetadata = {
            "columns": cls.builtin_column_options(),
            "filter_by": [
                {"field_name": "instances_with_tasks_completed_by_me", "field_value": True, "operator": "equals"},
                {"field_name": "process_status", "field_value": terminal_status_values, "operator": "equals"},
            ],
            "order_by": ["-start_in_seconds", "-id"],
        }
        system_report_completed_instances: ReportMetadata = {
            "columns": cls.builtin_column_options(),
            "filter_by": [
                {"field_name": "process_status", "field_value": terminal_status_values, "operator": "equals"},
            ],
            "order_by": ["-start_in_seconds", "-id"],
        }
        system_report_in_progress_instances_initiated_by_me: ReportMetadata = {
            "columns": [
                {"Header": "Id", "accessor": "id", "filterable": False},
                {
                    "Header": "Process",
                    "accessor": "process_model_display_name",
                    "filterable": False,
                },
                {"Header": "Task", "accessor": "task_title", "filterable": False},
                {"Header": "Waiting for", "accessor": "waiting_for", "filterable": False},
                {"Header": "Started", "accessor": "start_in_seconds", "filterable": False},
                {"Header": "Last updated", "accessor": "task_updated_at_in_seconds", "filterable": False},
                {"Header": "Last milestone", "accessor": "last_milestone_bpmn_name", "filterable": False},
                {"Header": "Status", "accessor": "status", "filterable": False},
            ],
            "filter_by": [
                {"field_name": "initiated_by_me", "field_value": True, "operator": "equals"},
                {"field_name": "process_status", "field_value": non_terminal_status_values, "operator": "equals"},
                {
                    "field_name": "with_oldest_open_task",
                    "field_value": True,
                    "operator": "equals",
                },
            ],
            "order_by": ["-start_in_seconds", "-id"],
        }
        system_report_in_progress_instances_with_tasks_for_me: ReportMetadata = {
            "columns": [
                {"Header": "Id", "accessor": "id", "filterable": False},
                {
                    "Header": "Process",
                    "accessor": "process_model_display_name",
                    "filterable": False,
                },
                {"Header": "Task", "accessor": "task_title", "filterable": False},
                {"Header": "Started by", "accessor": "process_initiator_username", "filterable": False},
                {"Header": "Started", "accessor": "start_in_seconds", "filterable": False},
                {"Header": "Last updated", "accessor": "task_updated_at_in_seconds", "filterable": False},
                {"Header": "Last milestone", "accessor": "last_milestone_bpmn_name", "filterable": False},
            ],
            "filter_by": [
                {"field_name": "instances_with_tasks_waiting_for_me", "field_value": True, "operator": "equals"},
                {"field_name": "process_status", "field_value": active_status_values, "operator": "equals"},
                {
                    "field_name": "with_oldest_open_task",
                    "field_value": True,
                    "operator": "equals",
                },
            ],
            "order_by": ["-start_in_seconds", "-id"],
        }
        system_report_in_progress_instances_with_tasks: ReportMetadata = {
            "columns": [
                {"Header": "Id", "accessor": "id", "filterable": False},
                {
                    "Header": "Process",
                    "accessor": "process_model_display_name",
                    "filterable": False,
                },
                {"Header": "Task", "accessor": "task_title", "filterable": False},
                {"Header": "Started by", "accessor": "process_initiator_username", "filterable": False},
                {"Header": "Started", "accessor": "start_in_seconds", "filterable": False},
                {"Header": "Last updated", "accessor": "task_updated_at_in_seconds", "filterable": False},
                {"Header": "Last milestone", "accessor": "last_milestone_bpmn_name", "filterable": False},
            ],
            "filter_by": [
                {"field_name": "process_status", "field_value": active_status_values, "operator": "equals"},
                {
                    "field_name": "with_oldest_open_task",
                    "field_value": True,
                    "operator": "equals",
                },
            ],
            "order_by": ["-start_in_seconds", "-id"],
        }

        temp_system_metadata_map = {
            "default": default,
            "system_report_completed_instances_initiated_by_me": system_report_completed_instances_initiated_by_me,
            "system_report_completed_instances_with_tasks_completed_by_me": (
                system_report_completed_instances_with_tasks_completed_by_me
            ),
            "system_report_completed_instances": system_report_completed_instances,
            "system_report_in_progress_instances_initiated_by_me": system_report_in_progress_instances_initiated_by_me,
            "system_report_in_progress_instances_with_tasks_for_me": system_report_in_progress_instances_with_tasks_for_me,
            "system_report_in_progress_instances_with_tasks": system_report_in_progress_instances_with_tasks,
        }
        if metadata_key not in temp_system_metadata_map:
            return None
        return_value: ReportMetadata = temp_system_metadata_map[metadata_key]
        return return_value

    @classmethod
    def process_instance_metadata_as_columns(cls, process_model_identifier: str | None = None) -> list[ReportMetadataColumn]:
        columns_for_metadata_query = db.session.query(ProcessInstanceMetadataModel.key.distinct()).order_by(  # type: ignore
            ProcessInstanceMetadataModel.key
        )
        if process_model_identifier:
            columns_for_metadata_query = columns_for_metadata_query.join(ProcessInstanceModel)  # type: ignore
            columns_for_metadata_query = columns_for_metadata_query.filter(
                ProcessInstanceModel.process_model_identifier == process_model_identifier
            )

        columns_for_metadata = columns_for_metadata_query.all()
        columns_for_metadata_strings: list[ReportMetadataColumn] = [
            {"Header": i[0], "accessor": i[0], "filterable": True} for i in columns_for_metadata
        ]
        return columns_for_metadata_strings

    @classmethod
    def compile_report(cls, report_metadata: ReportMetadata, user: UserModel) -> None:
        compiled_filters: list[FilterValue] = []
        old_filters = copy.deepcopy(report_metadata["filter_by"])
        for filter in old_filters:
            if filter["field_name"] == "initiated_by_me":
                compiled_filters.append(
                    {"field_name": "process_initiator_username", "field_value": user.username, "operator": "equals"}
                )
            else:
                compiled_filters.append(filter)

        report_metadata["filter_by"] = compiled_filters

    @classmethod
    def report_with_identifier(
        cls,
        user: UserModel,
        report_id: int | None = None,
        report_identifier: str | None = None,
    ) -> ProcessInstanceReportModel:
        if report_id is not None:
            process_instance_report = ProcessInstanceReportModel.query.filter_by(id=report_id, created_by_id=user.id).first()
            if process_instance_report is not None:
                return process_instance_report  # type: ignore

        if report_identifier is None:
            report_identifier = "default"
        process_instance_report = ProcessInstanceReportModel.query.filter_by(
            identifier=report_identifier, created_by_id=user.id
        ).first()

        if process_instance_report is not None:
            return process_instance_report  # type: ignore

        report_metadata = cls.system_metadata_map(report_identifier)
        if report_metadata is None:
            raise ProcessInstanceReportNotFoundError(
                f"Could not find a report with identifier '{report_identifier}' for user '{user.username}'"
            )
        cls.compile_report(report_metadata, user=user)

        process_instance_report = ProcessInstanceReportModel(
            identifier=report_identifier,
            created_by_id=user.id,
            report_metadata=report_metadata,
        )

        return process_instance_report  # type: ignore

    @classmethod
    def add_metadata_columns_to_process_instance(
        cls,
        process_instance_sqlalchemy_rows: list[sqlalchemy.engine.row.Row],  # type: ignore
        metadata_columns: list[ReportMetadataColumn],
    ) -> list[dict]:
        results = []
        for process_instance_row in process_instance_sqlalchemy_rows:
            process_instance_mapping = process_instance_row._mapping
            process_instance_dict = process_instance_row[0].serialized()
            for metadata_column in metadata_columns:
                if metadata_column["accessor"] not in process_instance_dict:
                    process_instance_dict[metadata_column["accessor"]] = process_instance_mapping[metadata_column["accessor"]]

            if "last_milestone_bpmn_name" in process_instance_mapping:
                process_instance_dict["last_milestone_bpmn_name"] = process_instance_mapping["last_milestone_bpmn_name"]

            results.append(process_instance_dict)
        return results

    @classmethod
    def add_human_task_fields(
        cls, process_instance_dicts: list[dict], restrict_human_tasks_to_user: UserModel | None = None
    ) -> list[dict]:
        fields_to_return = [
            "task_id",
            "task_title",
            "task_name",
            "potential_owner_usernames",
            "assigned_user_group_identifier",
        ]
        for process_instance_dict in process_instance_dicts:
            assigned_user = aliased(UserModel)
            human_task_query = (
                HumanTaskModel.query.filter_by(process_instance_id=process_instance_dict["id"], completed=False)
                .group_by(HumanTaskModel.id)
                .outerjoin(
                    HumanTaskUserModel,
                    HumanTaskModel.id == HumanTaskUserModel.human_task_id,
                )
                .outerjoin(assigned_user, assigned_user.id == HumanTaskUserModel.user_id)
                .outerjoin(GroupModel, GroupModel.id == HumanTaskModel.lane_assignment_id)
            )
            if restrict_human_tasks_to_user is not None:
                human_task_query = human_task_query.filter(HumanTaskUserModel.user_id == restrict_human_tasks_to_user.id)
            potential_owner_usernames_from_group_concat_or_similar = cls._get_potential_owner_usernames(assigned_user)
            human_task = (
                human_task_query.add_columns(
                    HumanTaskModel.task_id,
                    HumanTaskModel.task_name,
                    HumanTaskModel.task_title,
                    func.max(GroupModel.identifier).label("assigned_user_group_identifier"),
                    potential_owner_usernames_from_group_concat_or_similar,
                )
                .order_by(HumanTaskModel.id.asc())  # type: ignore
                .first()
            )
            if human_task is not None:
                for field in fields_to_return:
                    process_instance_dict[field] = getattr(human_task, field)
        return process_instance_dicts

    @classmethod
    def _get_potential_owner_usernames(cls, assigned_user: AliasedClass) -> Any:
        potential_owner_usernames_from_group_concat_or_similar = func.group_concat(assigned_user.username.distinct()).label(
            "potential_owner_usernames"
        )
        db_type = current_app.config.get("SPIFFWORKFLOW_BACKEND_DATABASE_TYPE")

        if db_type == "postgres":
            potential_owner_usernames_from_group_concat_or_similar = func.string_agg(
                assigned_user.username.distinct(), ", "
            ).label("potential_owner_usernames")

        return potential_owner_usernames_from_group_concat_or_similar

    @classmethod
    def get_column_names_for_model(cls, model: type[SpiffworkflowBaseDBModel]) -> list[str]:
        return [i.name for i in model.__table__.columns]

    @classmethod
    def process_instance_stock_columns(cls) -> list[str]:
        return cls.get_column_names_for_model(ProcessInstanceModel)

    @classmethod
    def non_metadata_columns(cls) -> list[str]:
        return cls.process_instance_stock_columns() + ["process_initiator_username", "last_milestone_bpmn_name", "summary"]

    @classmethod
    def builtin_column_options(cls) -> list[ReportMetadataColumn]:
        """Columns that are actually in the process instance table."""
        return_value: list[ReportMetadataColumn] = [
            {"Header": "Id", "accessor": "id", "filterable": False},
            {
                "Header": "Process",
                "accessor": "process_model_display_name",
                "filterable": False,
            },
            {"Header": "Start", "accessor": "start_in_seconds", "filterable": False},
            {"Header": "End", "accessor": "end_in_seconds", "filterable": False},
            {
                "Header": "Started by",
                "accessor": "process_initiator_username",
                "filterable": False,
            },
            {"Header": "Last milestone", "accessor": "last_milestone_bpmn_name", "filterable": False},
            {"Header": "Status", "accessor": "status", "filterable": False},
        ]
        return return_value

    @classmethod
    def system_report_column_options(cls) -> list[ReportMetadataColumn]:
        """Columns that are used with certain system reports."""
        return_value: list[ReportMetadataColumn] = [
            {"Header": "Task", "accessor": "task_title", "filterable": False},
            {"Header": "Waiting for", "accessor": "waiting_for", "filterable": False},
        ]
        return return_value

    @classmethod
    def get_filter_value(cls, filters: list[FilterValue], filter_key: str) -> Any:
        for filter in filters:
            if filter["field_name"] == filter_key and filter["field_value"] is not None:
                return filter["field_value"]

    @classmethod
    def check_filter_value(cls, filters: list[FilterValue], filter_key: str) -> Generator:
        value = cls.get_filter_value(filters, filter_key)
        if value is not None:
            yield value

    @classmethod
    def add_or_update_filter(cls, filters: list[FilterValue], new_filter: FilterValue) -> None:
        filter_found = False
        for filter in filters:
            if filter["field_name"] == new_filter["field_name"]:
                filter["field_value"] = new_filter["field_value"]
                filter_found = True
        if filter_found is False:
            filters.append(new_filter)

    # When we say we want to filter by "waiting for group" or "waiting for specific user," what we probably assume is that
    # there are human tasks that those people can actually complete right now.
    # We don't exactly have that in the query directly, but if you pass a filter for user_group_identifier, it will get into
    # this function, and if you pass any statuses, and if they are all "active" then it will do what you want, which is
    # to look for only HumanTaskModel.completed.is_(False). So...we should probably make the widget add filters for
    # both user_group_identifier and status. And we should make a method that does a similar thing for waiting for users.
    @classmethod
    def filter_by_user_group_identifier(
        cls,
        process_instance_query: Query,
        user_group_identifier: str,
        user: UserModel,
        human_task_already_joined: bool | None = False,
        process_status: str | None = None,
        instances_with_tasks_waiting_for_me: bool | None = False,
    ) -> Query:
        group_model_join_conditions = [GroupModel.id == HumanTaskModel.lane_assignment_id]
        if user_group_identifier:
            group_model_join_conditions.append(GroupModel.identifier == user_group_identifier)

        if human_task_already_joined is False:
            process_instance_query = process_instance_query.join(HumanTaskModel)  # type: ignore
        if process_status is not None:
            non_active_statuses = [s for s in process_status.split(",") if s not in ProcessInstanceModel.active_statuses()]
            if len(non_active_statuses) == 0:
                process_instance_query = process_instance_query.filter(HumanTaskModel.completed.is_(False))  # type: ignore
                # Check to make sure the task is not only available for the group but the user as well
                if instances_with_tasks_waiting_for_me is not True:
                    human_task_user_alias = aliased(HumanTaskUserModel)
                    process_instance_query = process_instance_query.join(  # type: ignore
                        human_task_user_alias,
                        and_(
                            human_task_user_alias.human_task_id == HumanTaskModel.id,
                            human_task_user_alias.user_id == user.id,
                        ),
                    )

        process_instance_query = process_instance_query.join(GroupModel, and_(*group_model_join_conditions))  # type: ignore
        process_instance_query = process_instance_query.join(  # type: ignore
            UserGroupAssignmentModel,
            UserGroupAssignmentModel.group_id == GroupModel.id,
        )

        # FIXME: this may be problematic
        # if user_group_identifier filter is set to something you are not in
        process_instance_query = process_instance_query.filter(UserGroupAssignmentModel.user_id == user.id)

        return process_instance_query

    @classmethod
    def filter_by_instances_with_tasks_waiting_for_me(
        cls,
        process_instance_query: Query,
        user: UserModel,
    ) -> Query:
        process_instance_query = process_instance_query.filter(ProcessInstanceModel.process_initiator_id != user.id)
        process_instance_query = process_instance_query.join(
            HumanTaskModel,
            and_(
                HumanTaskModel.process_instance_id == ProcessInstanceModel.id,
                HumanTaskModel.completed.is_(False),  # type: ignore
            ),
        ).join(
            HumanTaskUserModel,
            and_(HumanTaskUserModel.human_task_id == HumanTaskModel.id, HumanTaskUserModel.user_id == user.id),
        )

        user_group_assignment_for_lane_assignment = aliased(UserGroupAssignmentModel)
        process_instance_query = process_instance_query.outerjoin(  # type: ignore
            user_group_assignment_for_lane_assignment,
            and_(
                user_group_assignment_for_lane_assignment.group_id == HumanTaskModel.lane_assignment_id,
                user_group_assignment_for_lane_assignment.user_id == user.id,
            ),
        ).filter(
            # it should show up in your "Waiting for me" list IF:
            #   1) task is not assigned to a group OR
            #   2) you are not in the group
            # In the case of number 2, it probably means you were added to the task individually by an admin
            or_(
                HumanTaskModel.lane_assignment_id.is_(None),  # type: ignore
                user_group_assignment_for_lane_assignment.group_id.is_(None),
            )
        )

        return process_instance_query

    @classmethod
    def filter_by_instances_with_tasks_completed_by_me(
        cls,
        process_instance_query: Query,
        user: UserModel,
    ) -> Query:
        process_instance_query = process_instance_query.filter(ProcessInstanceModel.process_initiator_id != user.id)
        process_instance_query = process_instance_query.join(  # type: ignore
            HumanTaskModel,
            and_(
                HumanTaskModel.process_instance_id == ProcessInstanceModel.id,
                HumanTaskModel.completed_by_user_id == user.id,
            ),
        )
        return process_instance_query

    @classmethod
    def add_where_clauses_for_process_instance_metadata_filters(
        cls,
        process_instance_query: Query,
        report_metadata: ReportMetadata,
        instance_metadata_aliases: dict[str, Any],
    ) -> Query:
        for column in report_metadata["columns"]:
            if column["accessor"] in cls.non_metadata_columns():
                continue
            instance_metadata_alias = aliased(ProcessInstanceMetadataModel)
            instance_metadata_aliases[column["accessor"]] = instance_metadata_alias

            filters_for_column = []
            if "filter_by" in report_metadata:
                filters_for_column = [f for f in report_metadata["filter_by"] if f["field_name"] == column["accessor"]]
            isouter = True
            join_conditions = [
                ProcessInstanceModel.id == instance_metadata_alias.process_instance_id,
                instance_metadata_alias.key == column["accessor"],
            ]
            if len(filters_for_column) > 0:
                for filter_for_column in filters_for_column:
                    isouter = False
                    if "operator" not in filter_for_column or filter_for_column["operator"] == "equals":
                        join_conditions.append(instance_metadata_alias.value == filter_for_column["field_value"])
                    elif filter_for_column["operator"] == "not_equals":
                        join_conditions.append(instance_metadata_alias.value != filter_for_column["field_value"])
                    elif filter_for_column["operator"] == "greater_than_or_equal_to":
                        join_conditions.append(instance_metadata_alias.value >= filter_for_column["field_value"])
                    elif filter_for_column["operator"] == "less_than":
                        join_conditions.append(instance_metadata_alias.value < filter_for_column["field_value"])
                    elif filter_for_column["operator"] == "contains":
                        join_conditions.append(instance_metadata_alias.value.like(f"%{filter_for_column['field_value']}%"))
                    elif filter_for_column["operator"] == "is_empty":
                        # we still need to return results if the metadata value is null so make sure it's outer join
                        isouter = True
                        process_instance_query = process_instance_query.filter(
                            or_(instance_metadata_alias.value.is_(None), instance_metadata_alias.value == "")
                        )
                    elif filter_for_column["operator"] == "is_not_empty":
                        join_conditions.append(
                            or_(instance_metadata_alias.value.is_not(None), instance_metadata_alias.value != "")
                        )
            process_instance_query = process_instance_query.join(  # type: ignore
                instance_metadata_alias, and_(*join_conditions), isouter=isouter
            ).add_columns(func.max(instance_metadata_alias.value).label(column["accessor"]))
        return process_instance_query

    @classmethod
    def generate_order_by_query_array(
        cls,
        report_metadata: ReportMetadata,
        instance_metadata_aliases: dict[str, Any],
    ) -> list:
        order_by_query_array = []
        order_by_array = report_metadata["order_by"]
        if len(order_by_array) < 1:
            order_by_array = ProcessInstanceReportModel.default_order_by()
        for order_by_option in order_by_array:
            attribute = re.sub("^-", "", order_by_option)
            if attribute in cls.process_instance_stock_columns():
                if order_by_option.startswith("-"):
                    order_by_query_array.append(getattr(ProcessInstanceModel, attribute).desc())
                else:
                    order_by_query_array.append(getattr(ProcessInstanceModel, attribute).asc())
            elif attribute in instance_metadata_aliases:
                if order_by_option.startswith("-"):
                    order_by_query_array.append(func.max(instance_metadata_aliases[attribute].value).desc())
                else:
                    order_by_query_array.append(func.max(instance_metadata_aliases[attribute].value).asc())
        return order_by_query_array

    @classmethod
    def get_basic_query(
        cls,
        filters: list[FilterValue],
    ) -> Query:
        process_instance_query: Query = ProcessInstanceModel.query
        # Always join that hot user table for good performance at serialization time.
        process_instance_query = process_instance_query.options(selectinload(ProcessInstanceModel.process_initiator))

        for value in cls.check_filter_value(filters, "process_model_identifier"):
            process_model = ProcessModelService.get_process_model(
                f"{value}",
            )
            process_instance_query = process_instance_query.filter_by(process_model_identifier=process_model.id)

        # this can never happen. obviously the class has the columns it defines. this is just to appease mypy.
        if ProcessInstanceModel.start_in_seconds is None or ProcessInstanceModel.end_in_seconds is None:
            raise (
                ApiError(
                    error_code="unexpected_condition",
                    message="Something went very wrong",
                    status_code=500,
                )
            )

        for value in cls.check_filter_value(filters, "start_from"):
            process_instance_query = process_instance_query.filter(ProcessInstanceModel.start_in_seconds >= value)
        for value in cls.check_filter_value(filters, "start_to"):
            process_instance_query = process_instance_query.filter(ProcessInstanceModel.start_in_seconds <= value)
        for value in cls.check_filter_value(filters, "end_from"):
            process_instance_query = process_instance_query.filter(ProcessInstanceModel.end_in_seconds >= value)
        for value in cls.check_filter_value(filters, "end_to"):
            process_instance_query = process_instance_query.filter(ProcessInstanceModel.end_in_seconds <= value)

        has_active_status = cls.get_filter_value(filters, "has_active_status")
        if has_active_status:
            process_instance_query = process_instance_query.filter(
                ProcessInstanceModel.status.in_(ProcessInstanceModel.active_statuses())  # type: ignore
            )

        for value in cls.check_filter_value(filters, "process_initiator_username"):
            initiator = UserModel.query.filter_by(username=value).first()
            process_initiator_id = -1
            if initiator:
                process_initiator_id = initiator.id
            process_instance_query = process_instance_query.filter_by(process_initiator_id=process_initiator_id)
        return process_instance_query

    @classmethod
    def run_process_instance_report(
        cls,
        report_metadata: ReportMetadata,
        user: UserModel | None = None,
        page: int = 1,
        per_page: int = 100,
    ) -> dict:
        restrict_human_tasks_to_user = None
        filters = report_metadata["filter_by"]
        process_instance_query = cls.get_basic_query(filters)

        process_status = cls.get_filter_value(filters, "process_status")
        if process_status is not None:
            process_instance_query = process_instance_query.filter(
                ProcessInstanceModel.status.in_(process_status.split(","))  # type: ignore
            )

        instances_with_tasks_completed_by_me = cls.get_filter_value(filters, "instances_with_tasks_completed_by_me")
        instances_with_tasks_waiting_for_me = cls.get_filter_value(filters, "instances_with_tasks_waiting_for_me")
        user_group_identifier = cls.get_filter_value(filters, "user_group_identifier")

        # builtin only - for the for-me paths
        with_relation_to_me = cls.get_filter_value(filters, "with_relation_to_me")

        if (
            not instances_with_tasks_completed_by_me
            and not user_group_identifier
            and not instances_with_tasks_waiting_for_me
            and with_relation_to_me is True
        ):
            if user is None:
                raise ProcessInstanceReportCannotBeRunError("A user must be specified to run report with with_relation_to_me")
            process_instance_query = process_instance_query.outerjoin(HumanTaskModel).outerjoin(  # type: ignore
                HumanTaskUserModel,
                and_(
                    HumanTaskModel.id == HumanTaskUserModel.human_task_id,
                    HumanTaskUserModel.user_id == user.id,
                ),
            )
            process_instance_query = process_instance_query.filter(
                or_(
                    HumanTaskUserModel.id.is_not(None),
                    ProcessInstanceModel.process_initiator_id == user.id,
                )
            )

        if instances_with_tasks_completed_by_me is True and instances_with_tasks_waiting_for_me is True:
            raise ProcessInstanceReportMetadataInvalidError(
                "Cannot set both 'instances_with_tasks_completed_by_me' and 'instances_with_tasks_waiting_for_me' to"
                " true. You must choose one."
            )

        # ensure we only join with HumanTaskModel once
        human_task_already_joined = False

        if instances_with_tasks_completed_by_me is True:
            if user is None:
                raise ProcessInstanceReportCannotBeRunError(
                    "A user must be specified to run report with instances_with_tasks_completed_by_me."
                )
            process_instance_query = cls.filter_by_instances_with_tasks_completed_by_me(process_instance_query, user)
            human_task_already_joined = True

        # this excludes some tasks you can complete, because that's the way the requirements were described.
        # if it's assigned to one of your groups, it does not get returned by this query.
        if instances_with_tasks_waiting_for_me is True:
            if user is None:
                raise ProcessInstanceReportCannotBeRunError(
                    "A user must be specified to run report with instances_with_tasks_waiting_for_me."
                )
            human_task_already_joined = True
            restrict_human_tasks_to_user = user
            process_instance_query = cls.filter_by_instances_with_tasks_waiting_for_me(
                process_instance_query=process_instance_query,
                user=user,
            )

        if user_group_identifier is not None:
            if user is None:
                raise ProcessInstanceReportCannotBeRunError("A user must be specified to run report with a group identifier.")
            process_instance_query = cls.filter_by_user_group_identifier(
                process_instance_query=process_instance_query,
                user_group_identifier=user_group_identifier,
                user=user,
                human_task_already_joined=human_task_already_joined,
                process_status=process_status,
                instances_with_tasks_waiting_for_me=instances_with_tasks_waiting_for_me,
            )

        instance_metadata_aliases: dict[str, Any] = {}
        if report_metadata["columns"] is None or len(report_metadata["columns"]) < 1:
            report_metadata["columns"] = cls.builtin_column_options()
        process_instance_query = cls.add_where_clauses_for_process_instance_metadata_filters(
            process_instance_query, report_metadata, instance_metadata_aliases
        )
        order_by_query_array = cls.generate_order_by_query_array(report_metadata, instance_metadata_aliases)

        process_instances = (
            process_instance_query.group_by(ProcessInstanceModel.id)  # type: ignore
            .add_columns(ProcessInstanceModel.id)
            .order_by(*order_by_query_array)
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        results = cls.add_metadata_columns_to_process_instance(process_instances.items, report_metadata["columns"])

        for value in cls.check_filter_value(filters, "with_oldest_open_task"):
            if value is True:
                results = cls.add_human_task_fields(results, restrict_human_tasks_to_user=restrict_human_tasks_to_user)

        report_metadata["filter_by"] = filters
        response_json = {
            "report_metadata": report_metadata,
            "results": results,
            "pagination": {
                "count": len(results),
                "total": process_instances.total,
                "pages": process_instances.pages,
            },
        }
        return response_json
