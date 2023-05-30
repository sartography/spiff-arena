"""Process_instance_report_service."""
import copy
import re
from collections.abc import Generator
from typing import Any

import sqlalchemy
from flask import current_app
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_metadata import ProcessInstanceMetadataModel
from spiffworkflow_backend.models.process_instance_report import FilterValue
from spiffworkflow_backend.models.process_instance_report import ProcessInstanceReportModel
from spiffworkflow_backend.models.process_instance_report import ReportMetadata
from spiffworkflow_backend.models.process_instance_report import ReportMetadataColumn
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user_group_assignment import UserGroupAssignmentModel
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy.orm import aliased
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.util import AliasedClass


class ProcessInstanceReportNotFoundError(Exception):
    pass


class ProcessInstanceReportMetadataInvalidError(Exception):
    pass


class ProcessInstanceReportService:
    """ProcessInstanceReportService."""

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
                {"Header": "Start Time", "accessor": "start_in_seconds", "filterable": False},
                {"Header": "End Time", "accessor": "end_in_seconds", "filterable": False},
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
                {"Header": "Waiting For", "accessor": "waiting_for", "filterable": False},
                {"Header": "Started", "accessor": "start_in_seconds", "filterable": False},
                {"Header": "Last Updated", "accessor": "task_updated_at_in_seconds", "filterable": False},
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
                {"Header": "Started By", "accessor": "process_initiator_username", "filterable": False},
                {"Header": "Started", "accessor": "start_in_seconds", "filterable": False},
                {"Header": "Last Updated", "accessor": "task_updated_at_in_seconds", "filterable": False},
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
                {"Header": "Started By", "accessor": "process_initiator_username", "filterable": False},
                {"Header": "Started", "accessor": "start_in_seconds", "filterable": False},
                {"Header": "Last Updated", "accessor": "task_updated_at_in_seconds", "filterable": False},
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
            "system_report_in_progress_instances_with_tasks_for_me": (
                system_report_in_progress_instances_with_tasks_for_me
            ),
            "system_report_in_progress_instances_with_tasks": system_report_in_progress_instances_with_tasks,
        }
        if metadata_key not in temp_system_metadata_map:
            return None
        return_value: ReportMetadata = temp_system_metadata_map[metadata_key]
        return return_value

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
            process_instance_report = ProcessInstanceReportModel.query.filter_by(
                id=report_id, created_by_id=user.id
            ).first()
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
        """Add_metadata_columns_to_process_instance."""
        results = []
        cls.non_metadata_columns()
        for process_instance_row in process_instance_sqlalchemy_rows:
            process_instance_mapping = process_instance_row._mapping
            process_instance_dict = process_instance_row[0].serialized
            for metadata_column in metadata_columns:
                if metadata_column["accessor"] not in process_instance_dict:
                    process_instance_dict[metadata_column["accessor"]] = process_instance_mapping[
                        metadata_column["accessor"]
                    ]

            results.append(process_instance_dict)
        return results

    @classmethod
    def add_human_task_fields(cls, process_instance_dicts: list[dict]) -> list[dict]:
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
        """_get_potential_owner_usernames."""
        potential_owner_usernames_from_group_concat_or_similar = func.group_concat(
            assigned_user.username.distinct()
        ).label("potential_owner_usernames")
        db_type = current_app.config.get("SPIFFWORKFLOW_BACKEND_DATABASE_TYPE")

        if db_type == "postgres":
            potential_owner_usernames_from_group_concat_or_similar = func.string_agg(
                assigned_user.username.distinct(), ", "
            ).label("potential_owner_usernames")

        return potential_owner_usernames_from_group_concat_or_similar

    @classmethod
    def get_column_names_for_model(cls, model: type[SpiffworkflowBaseDBModel]) -> list[str]:
        """Get_column_names_for_model."""
        return [i.name for i in model.__table__.columns]

    @classmethod
    def process_instance_stock_columns(cls) -> list[str]:
        return cls.get_column_names_for_model(ProcessInstanceModel)

    @classmethod
    def non_metadata_columns(cls) -> list[str]:
        return cls.process_instance_stock_columns() + ["process_initiator_username"]

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
                "Header": "Started By",
                "accessor": "process_initiator_username",
                "filterable": False,
            },
            {"Header": "Status", "accessor": "status", "filterable": False},
        ]
        return return_value

    @classmethod
    def system_report_column_options(cls) -> list[ReportMetadataColumn]:
        """Columns that are used with certain system reports."""
        return_value: list[ReportMetadataColumn] = [
            {"Header": "Task", "accessor": "task_title", "filterable": False},
            {"Header": "Waiting For", "accessor": "waiting_for", "filterable": False},
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

    @classmethod
    def run_process_instance_report(
        cls,
        report_metadata: ReportMetadata,
        user: UserModel,
        page: int = 1,
        per_page: int = 100,
    ) -> dict:
        process_instance_query = ProcessInstanceModel.query
        # Always join that hot user table for good performance at serialization time.
        process_instance_query = process_instance_query.options(selectinload(ProcessInstanceModel.process_initiator))
        filters = report_metadata["filter_by"]

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

        process_status = cls.get_filter_value(filters, "process_status")
        if process_status is not None:
            process_instance_query = process_instance_query.filter(
                ProcessInstanceModel.status.in_(process_status.split(","))  # type: ignore
            )

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
            process_instance_query = process_instance_query.outerjoin(HumanTaskModel).outerjoin(
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
            process_instance_query = process_instance_query.filter(
                ProcessInstanceModel.process_initiator_id != user.id
            )
            process_instance_query = process_instance_query.join(
                HumanTaskModel,
                and_(
                    HumanTaskModel.process_instance_id == ProcessInstanceModel.id,
                    HumanTaskModel.completed_by_user_id == user.id,
                ),
            )
            human_task_already_joined = True

        # this excludes some tasks you can complete, because that's the way the requirements were described.
        # if it's assigned to one of your groups, it does not get returned by this query.
        if instances_with_tasks_waiting_for_me is True:
            process_instance_query = process_instance_query.filter(
                ProcessInstanceModel.process_initiator_id != user.id
            )
            process_instance_query = process_instance_query.join(
                HumanTaskModel,
                and_(
                    HumanTaskModel.process_instance_id == ProcessInstanceModel.id,
                    HumanTaskModel.lane_assignment_id.is_(None),  # type: ignore
                    HumanTaskModel.completed.is_(False),  # type: ignore
                ),
            ).join(
                HumanTaskUserModel,
                and_(HumanTaskUserModel.human_task_id == HumanTaskModel.id, HumanTaskUserModel.user_id == user.id),
            )
            human_task_already_joined = True

        if user_group_identifier is not None:
            group_model_join_conditions = [GroupModel.id == HumanTaskModel.lane_assignment_id]
            if user_group_identifier:
                group_model_join_conditions.append(GroupModel.identifier == user_group_identifier)

            if human_task_already_joined is False:
                process_instance_query = process_instance_query.join(HumanTaskModel)
            if process_status is not None:
                non_active_statuses = [
                    s for s in process_status.split(",") if s not in ProcessInstanceModel.active_statuses()
                ]
                if len(non_active_statuses) == 0:
                    process_instance_query = process_instance_query.filter(
                        HumanTaskModel.completed.is_(False)  # type: ignore
                    )

            process_instance_query = process_instance_query.join(GroupModel, and_(*group_model_join_conditions))
            process_instance_query = process_instance_query.join(
                UserGroupAssignmentModel,
                UserGroupAssignmentModel.group_id == GroupModel.id,
            )
            process_instance_query = process_instance_query.filter(UserGroupAssignmentModel.user_id == user.id)

        instance_metadata_aliases = {}
        if report_metadata["columns"] is None or len(report_metadata["columns"]) < 1:
            report_metadata["columns"] = cls.builtin_column_options()

        for column in report_metadata["columns"]:
            if column["accessor"] in cls.non_metadata_columns():
                continue
            instance_metadata_alias = aliased(ProcessInstanceMetadataModel)
            instance_metadata_aliases[column["accessor"]] = instance_metadata_alias

            filter_for_column = None
            if "filter_by" in report_metadata:
                filter_for_column = next(
                    (f for f in report_metadata["filter_by"] if f["field_name"] == column["accessor"]),
                    None,
                )
            isouter = True
            conditions = [
                ProcessInstanceModel.id == instance_metadata_alias.process_instance_id,
                instance_metadata_alias.key == column["accessor"],
            ]
            if filter_for_column:
                isouter = False
                conditions.append(instance_metadata_alias.value == filter_for_column["field_value"])
            process_instance_query = process_instance_query.join(
                instance_metadata_alias, and_(*conditions), isouter=isouter
            ).add_columns(func.max(instance_metadata_alias.value).label(column["accessor"]))

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

        process_instances = (
            process_instance_query.group_by(ProcessInstanceModel.id)
            .add_columns(ProcessInstanceModel.id)
            .order_by(*order_by_query_array)
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        results = cls.add_metadata_columns_to_process_instance(process_instances.items, report_metadata["columns"])

        for value in cls.check_filter_value(filters, "with_oldest_open_task"):
            if value is True:
                results = cls.add_human_task_fields(results)

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
