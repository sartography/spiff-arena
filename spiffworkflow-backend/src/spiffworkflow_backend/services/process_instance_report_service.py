"""Process_instance_report_service."""
import re
from dataclasses import dataclass
from typing import Any, Generator, Iterable
from typing import Optional
from typing import Type

import sqlalchemy
from flask import current_app
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy.orm import aliased
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.util import AliasedClass

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_metadata import (
    ProcessInstanceMetadataModel,
)
from spiffworkflow_backend.models.process_instance_report import (
    FilterValue,
    ProcessInstanceReportModel,
    ReportMetadata,
)
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user_group_assignment import UserGroupAssignmentModel
from spiffworkflow_backend.services.process_model_service import ProcessModelService


class ProcessInstanceReportNotFoundError(Exception):
    """ProcessInstanceReportNotFoundError."""


# @dataclass
# class ProcessInstanceReportFilter:
#     """ProcessInstanceReportFilter."""
#
#     process_model_identifier: Optional[str] = None
#     user_group_identifier: Optional[str] = None
#     start_from: Optional[int] = None
#     start_to: Optional[int] = None
#     end_from: Optional[int] = None
#     end_to: Optional[int] = None
#     process_status: Optional[list[str]] = None
#     initiated_by_me: Optional[bool] = None
#     has_terminal_status: Optional[bool] = None
#     has_active_status: Optional[bool] = None
#     with_tasks_completed_by_me: Optional[bool] = None
#     with_tasks_i_can_complete: Optional[bool] = None
#     with_tasks_assigned_to_my_group: Optional[bool] = None
#     with_relation_to_me: Optional[bool] = None
#     process_initiator_username: Optional[str] = None
#     report_column_list: Optional[list] = None
#     report_filter_by_list: Optional[list] = None
#     oldest_open_human_task_fields: Optional[list] = None
#
#     def to_dict(self) -> dict[str, str]:
#         """To_dict."""
#         d = {}
#
#         if self.process_model_identifier is not None:
#             d["process_model_identifier"] = self.process_model_identifier
#         if self.user_group_identifier is not None:
#             d["user_group_identifier"] = self.user_group_identifier
#         if self.start_from is not None:
#             d["start_from"] = str(self.start_from)
#         if self.start_to is not None:
#             d["start_to"] = str(self.start_to)
#         if self.end_from is not None:
#             d["end_from"] = str(self.end_from)
#         if self.end_to is not None:
#             d["end_to"] = str(self.end_to)
#         if self.process_status is not None:
#             d["process_status"] = ",".join(self.process_status)
#         if self.initiated_by_me is not None:
#             d["initiated_by_me"] = str(self.initiated_by_me).lower()
#         if self.has_terminal_status is not None:
#             d["has_terminal_status"] = str(self.has_terminal_status).lower()
#         if self.has_active_status is not None:
#             d["has_active_status"] = str(self.has_active_status).lower()
#         if self.with_tasks_completed_by_me is not None:
#             d["with_tasks_completed_by_me"] = str(self.with_tasks_completed_by_me).lower()
#         if self.with_tasks_i_can_complete is not None:
#             d["with_tasks_i_can_complete"] = str(self.with_tasks_i_can_complete).lower()
#         if self.with_tasks_assigned_to_my_group is not None:
#             d["with_tasks_assigned_to_my_group"] = str(self.with_tasks_assigned_to_my_group).lower()
#         if self.with_relation_to_me is not None:
#             d["with_relation_to_me"] = str(self.with_relation_to_me).lower()
#         if self.process_initiator_username is not None:
#             d["process_initiator_username"] = str(self.process_initiator_username)
#         if self.report_column_list is not None:
#             d["report_column_list"] = str(self.report_column_list)
#         if self.report_filter_by_list is not None:
#             d["report_filter_by_list"] = str(self.report_filter_by_list)
#         if self.oldest_open_human_task_fields is not None:
#             d["oldest_open_human_task_fields"] = str(self.oldest_open_human_task_fields)
#
#         return d


class ProcessInstanceReportService:
    """ProcessInstanceReportService."""

    @classmethod
    def system_metadata_map(cls, metadata_key: str) -> Optional[dict[str, Any]]:
        """System_metadata_map."""
        # TODO replace with system reports that are loaded on launch (or similar)
        temp_system_metadata_map = {
            "default": {
                "columns": cls.builtin_column_options(),
                "filter_by": [],
                "order_by": ["-start_in_seconds", "-id"],
            },
            "system_report_completed_instances_initiated_by_me": {
                "columns": [
                    {"Header": "id", "accessor": "id"},
                    {
                        "Header": "process_model_display_name",
                        "accessor": "process_model_display_name",
                    },
                    {"Header": "start_in_seconds", "accessor": "start_in_seconds"},
                    {"Header": "end_in_seconds", "accessor": "end_in_seconds"},
                    {"Header": "status", "accessor": "status"},
                ],
                "filter_by": [
                    {"field_name": "initiated_by_me", "field_value": "true"},
                    {"field_name": "has_terminal_status", "field_value": "true"},
                ],
                "order_by": ["-start_in_seconds", "-id"],
            },
            "system_report_completed_instances_with_tasks_completed_by_me": {
                "columns": cls.builtin_column_options(),
                "filter_by": [
                    {"field_name": "with_tasks_completed_by_me", "field_value": "true"},
                    {"field_name": "has_terminal_status", "field_value": "true"},
                ],
                "order_by": ["-start_in_seconds", "-id"],
            },
            "system_report_completed_instances_with_tasks_completed_by_my_groups": {
                "columns": cls.builtin_column_options(),
                "filter_by": [
                    {
                        "field_name": "with_tasks_assigned_to_my_group",
                        "field_value": "true",
                    },
                    {"field_name": "has_terminal_status", "field_value": "true"},
                ],
                "order_by": ["-start_in_seconds", "-id"],
            },
            "system_report_in_progress_instances_initiated_by_me": {
                "columns": [
                    {"Header": "id", "accessor": "id"},
                    {
                        "Header": "process_model_display_name",
                        "accessor": "process_model_display_name",
                    },
                    {"Header": "Task", "accessor": "task_title"},
                    {"Header": "Waiting For", "accessor": "waiting_for"},
                    {"Header": "Started", "accessor": "start_in_seconds"},
                    {"Header": "Last Updated", "accessor": "updated_at_in_seconds"},
                    {"Header": "status", "accessor": "status"},
                ],
                "filter_by": [
                    {"field_name": "initiated_by_me", "field_value": "true"},
                    {"field_name": "has_terminal_status", "field_value": "false"},
                    {
                        "field_name": "oldest_open_human_task_fields",
                        "field_value": (
                            "task_id,task_title,task_name,potential_owner_usernames,assigned_user_group_identifier"
                        ),
                    },
                ],
                "order_by": ["-start_in_seconds", "-id"],
            },
            "system_report_in_progress_instances_with_tasks_for_me": {
                "columns": [
                    {"Header": "id", "accessor": "id"},
                    {
                        "Header": "process_model_display_name",
                        "accessor": "process_model_display_name",
                    },
                    {"Header": "Task", "accessor": "task_title"},
                    {"Header": "Started By", "accessor": "process_initiator_username"},
                    {"Header": "Started", "accessor": "start_in_seconds"},
                    {"Header": "Last Updated", "accessor": "updated_at_in_seconds"},
                ],
                "filter_by": [
                    {"field_name": "with_tasks_i_can_complete", "field_value": "true"},
                    {"field_name": "has_active_status", "field_value": "true"},
                    {
                        "field_name": "oldest_open_human_task_fields",
                        "field_value": "task_id,task_title,task_name",
                    },
                ],
                "order_by": ["-start_in_seconds", "-id"],
            },
            "system_report_in_progress_instances_with_tasks_for_my_group": {
                "columns": [
                    {"Header": "id", "accessor": "id"},
                    {
                        "Header": "process_model_display_name",
                        "accessor": "process_model_display_name",
                    },
                    {"Header": "Task", "accessor": "task_title"},
                    {"Header": "Started By", "accessor": "process_initiator_username"},
                    {"Header": "Started", "accessor": "start_in_seconds"},
                    {"Header": "Last Updated", "accessor": "updated_at_in_seconds"},
                ],
                "filter_by": [
                    {
                        "field_name": "with_tasks_assigned_to_my_group",
                        "field_value": "true",
                    },
                    {"field_name": "has_active_status", "field_value": "true"},
                    {
                        "field_name": "oldest_open_human_task_fields",
                        "field_value": "task_id,task_title,task_name",
                    },
                ],
                "order_by": ["-start_in_seconds", "-id"],
            },
        }

        if metadata_key not in temp_system_metadata_map:
            return None
        return temp_system_metadata_map[metadata_key]

    @classmethod
    def report_with_identifier(
        cls,
        user: UserModel,
        report_id: Optional[int] = None,
        report_identifier: Optional[str] = None,
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

        process_instance_report = ProcessInstanceReportModel(
            identifier=report_identifier,
            created_by_id=user.id,
            report_metadata=report_metadata,
        )

        return process_instance_report  # type: ignore

    # @classmethod
    # def filter_by_to_dict(cls, process_instance_report: ProcessInstanceReportModel) -> dict[str, str]:
    #     """Filter_by_to_dict."""
    #     metadata = process_instance_report.report_metadata
    #     filter_by = metadata.get("filter_by", [])
    #     filters = {d["field_name"]: d["field_value"] for d in filter_by if "field_name" in d and "field_value" in d}
    #     return filters
    #
    # @classmethod
    # def filter_from_metadata(cls, process_instance_report: ProcessInstanceReportModel) -> ProcessInstanceReportFilter:
    #     """Filter_from_metadata."""
    #     filters = cls.filter_by_to_dict(process_instance_report)
    #
    #     def bool_value(key: str) -> Optional[bool]:
    #         """Bool_value."""
    #         if key not in filters:
    #             return None
    #         # bool returns True if not an empty string so check explicitly for false
    #         if filters[key] in ["false", "False"]:
    #             return False
    #         return bool(filters[key])
    #
    #     def int_value(key: str) -> Optional[int]:
    #         """Int_value."""
    #         return int(filters[key]) if key in filters else None
    #
    #     def list_value(key: str) -> Optional[list[str]]:
    #         return filters[key].split(",") if key in filters else None
    #
    #     process_model_identifier = filters.get("process_model_identifier")
    #     user_group_identifier = filters.get("user_group_identifier")
    #     start_from = int_value("start_from")
    #     start_to = int_value("start_to")
    #     end_from = int_value("end_from")
    #     end_to = int_value("end_to")
    #     process_status = list_value("process_status")
    #     initiated_by_me = bool_value("initiated_by_me")
    #     has_terminal_status = bool_value("has_terminal_status")
    #     has_active_status = bool_value("has_active_status")
    #     with_tasks_completed_by_me = bool_value("with_tasks_completed_by_me")
    #     with_tasks_i_can_complete = bool_value("with_tasks_i_can_complete")
    #     with_tasks_assigned_to_my_group = bool_value("with_tasks_assigned_to_my_group")
    #     with_relation_to_me = bool_value("with_relation_to_me")
    #     process_initiator_username = filters.get("process_initiator_username")
    #     report_column_list = list_value("report_column_list")
    #     report_filter_by_list = list_value("report_filter_by_list")
    #     oldest_open_human_task_fields = list_value("oldest_open_human_task_fields")
    #
    #     report_filter = ProcessInstanceReportFilter(
    #         process_model_identifier=process_model_identifier,
    #         user_group_identifier=user_group_identifier,
    #         start_from=start_from,
    #         start_to=start_to,
    #         end_from=end_from,
    #         end_to=end_to,
    #         process_status=process_status,
    #         initiated_by_me=initiated_by_me,
    #         has_terminal_status=has_terminal_status,
    #         has_active_status=has_active_status,
    #         with_tasks_completed_by_me=with_tasks_completed_by_me,
    #         with_tasks_i_can_complete=with_tasks_i_can_complete,
    #         with_tasks_assigned_to_my_group=with_tasks_assigned_to_my_group,
    #         with_relation_to_me=with_relation_to_me,
    #         process_initiator_username=process_initiator_username,
    #         report_column_list=report_column_list,
    #         report_filter_by_list=report_filter_by_list,
    #         oldest_open_human_task_fields=oldest_open_human_task_fields,
    #     )
    #
    #     return report_filter
    #
    # @classmethod
    # def filter_from_metadata_with_overrides(
    #     cls,
    #     process_instance_report: ProcessInstanceReportModel,
    #     process_model_identifier: Optional[str] = None,
    #     user_group_identifier: Optional[str] = None,
    #     start_from: Optional[int] = None,
    #     start_to: Optional[int] = None,
    #     end_from: Optional[int] = None,
    #     end_to: Optional[int] = None,
    #     process_status: Optional[str] = None,
    #     initiated_by_me: Optional[bool] = None,
    #     has_terminal_status: Optional[bool] = None,
    #     has_active_status: Optional[bool] = None,
    #     with_tasks_completed_by_me: Optional[bool] = None,
    #     with_tasks_i_can_complete: Optional[bool] = None,
    #     with_tasks_assigned_to_my_group: Optional[bool] = None,
    #     with_relation_to_me: Optional[bool] = None,
    #     process_initiator_username: Optional[str] = None,
    #     report_column_list: Optional[list] = None,
    #     report_filter_by_list: Optional[list] = None,
    #     oldest_open_human_task_fields: Optional[list] = None,
    # ) -> ProcessInstanceReportFilter:
    #     """Filter_from_metadata_with_overrides."""
    #     report_filter = cls.filter_from_metadata(process_instance_report)
    #
    #     if process_model_identifier is not None:
    #         report_filter.process_model_identifier = process_model_identifier
    #     if user_group_identifier is not None:
    #         report_filter.user_group_identifier = user_group_identifier
    #     if start_from is not None:
    #         report_filter.start_from = start_from
    #     if start_to is not None:
    #         report_filter.start_to = start_to
    #     if end_from is not None:
    #         report_filter.end_from = end_from
    #     if end_to is not None:
    #         report_filter.end_to = end_to
    #     if process_status is not None:
    #         report_filter.process_status = process_status.split(",")
    #     if initiated_by_me is not None:
    #         report_filter.initiated_by_me = initiated_by_me
    #     if has_terminal_status is not None:
    #         report_filter.has_terminal_status = has_terminal_status
    #     if has_active_status is not None:
    #         report_filter.has_active_status = has_active_status
    #     if with_tasks_completed_by_me is not None:
    #         report_filter.with_tasks_completed_by_me = with_tasks_completed_by_me
    #     if with_tasks_i_can_complete is not None:
    #         report_filter.with_tasks_i_can_complete = with_tasks_i_can_complete
    #     if process_initiator_username is not None:
    #         report_filter.process_initiator_username = process_initiator_username
    #     if report_column_list is not None:
    #         report_filter.report_column_list = report_column_list
    #     if report_filter_by_list is not None:
    #         report_filter.report_filter_by_list = report_filter_by_list
    #     if oldest_open_human_task_fields is not None:
    #         report_filter.oldest_open_human_task_fields = oldest_open_human_task_fields
    #     if with_tasks_assigned_to_my_group is not None:
    #         report_filter.with_tasks_assigned_to_my_group = with_tasks_assigned_to_my_group
    #     if with_relation_to_me is not None:
    #         report_filter.with_relation_to_me = with_relation_to_me
    #
    #     return report_filter

    @classmethod
    def add_metadata_columns_to_process_instance(
        cls,
        process_instance_sqlalchemy_rows: list[sqlalchemy.engine.row.Row],  # type: ignore
        metadata_columns: list[dict],
    ) -> list[dict]:
        """Add_metadata_columns_to_process_instance."""
        results = []
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
    def add_human_task_fields(
        cls, process_instance_dicts: list[dict], oldest_open_human_task_fields: list
    ) -> list[dict]:
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
                for field in oldest_open_human_task_fields:
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
    def get_column_names_for_model(cls, model: Type[SpiffworkflowBaseDBModel]) -> list[str]:
        """Get_column_names_for_model."""
        return [i.name for i in model.__table__.columns]

    @classmethod
    def builtin_column_options(cls) -> list[dict]:
        """Builtin_column_options."""
        return [
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

    @classmethod
    def get_filter_value(cls, filters: list[FilterValue], filter_key: str) -> Any:
        for filter in filters:
            if filter['field_name'] == filter_key and filter['field_value'] is not None:
                return filter['field_value']

    @classmethod
    def check_filter_value(cls, filters: list[FilterValue], filter_key: str) -> Generator:
        value = cls.get_filter_value(filters, filter_key)
        if value is not None:
            yield value

    @classmethod
    def run_process_instance_report(
        cls,
        # report_filter: ProcessInstanceReportFilter,
        report_metadata: ReportMetadata,
        process_instance_report: ProcessInstanceReportModel,
        user: UserModel,
        page: int = 1,
        per_page: int = 100,
    ) -> dict:
        process_instance_query = ProcessInstanceModel.query
        # Always join that hot user table for good performance at serialization time.
        process_instance_query = process_instance_query.options(selectinload(ProcessInstanceModel.process_initiator))
        filters = report_metadata['filter_by']

        for value in cls.check_filter_value(filters, 'process_model_identifier'):
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

        for value in cls.check_filter_value(filters, 'start_from'):
            process_instance_query = process_instance_query.filter(
                ProcessInstanceModel.start_in_seconds >= value
            )
        for value in cls.check_filter_value(filters, 'start_to'):
            process_instance_query = process_instance_query.filter(
                ProcessInstanceModel.start_in_seconds <= value
            )
        for value in cls.check_filter_value(filters, 'end_from'):
            process_instance_query = process_instance_query.filter(
                ProcessInstanceModel.end_in_seconds >= value
            )
        for value in cls.check_filter_value(filters, 'end_to'):
            process_instance_query = process_instance_query.filter(
                ProcessInstanceModel.end_in_seconds <= value
            )
        for value in cls.check_filter_value(filters, 'process_status'):
            process_instance_query = process_instance_query.filter(
                ProcessInstanceModel.status.in_(value.split(','))  # type: ignore
            )

        for value in cls.check_filter_value(filters, 'initiated_by_me'):
            if value is True:
                process_instance_query = process_instance_query.filter_by(process_initiator=user)

        for value in cls.check_filter_value(filters, 'has_terminal_status'):
            if value is True:
                process_instance_query = process_instance_query.filter(
                    ProcessInstanceModel.status.in_(ProcessInstanceModel.terminal_statuses())  # type: ignore
                )
            elif value is False:
                process_instance_query = process_instance_query.filter(
                    ProcessInstanceModel.status.not_in(ProcessInstanceModel.terminal_statuses())  # type: ignore
                )
        for value in cls.check_filter_value(filters, 'has_active_status'):
            if value is True:
                process_instance_query = process_instance_query.filter(
                    ProcessInstanceModel.status.in_(ProcessInstanceModel.active_statuses())  # type: ignore
                )

        for value in cls.check_filter_value(filters, 'process_initiator_username'):
            initiator = UserModel.query.filter_by(username=value).first()
            process_initiator_id = -1
            if initiator:
                process_initiator_id = initiator.id
            process_instance_query = process_instance_query.filter_by(process_initiator_id=process_initiator_id)

        with_tasks_completed_by_me = cls.get_filter_value(filters, 'with_tasks_completed_by_me')
        with_tasks_assigned_to_my_group = cls.get_filter_value(filters, 'with_tasks_assigned_to_my_group')
        with_tasks_i_can_complete = cls.get_filter_value(filters, 'with_tasks_i_can_complete')
        with_relation_to_me = cls.get_filter_value(filters, 'with_relation_to_me')
        has_active_status = cls.get_filter_value(filters, 'has_active_status')
        user_group_identifier = cls.get_filter_value(filters, 'user_group_identifier')
        if (
            not with_tasks_completed_by_me
            and not with_tasks_assigned_to_my_group
            and not with_tasks_i_can_complete
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

        if with_tasks_completed_by_me is True:
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

        if with_tasks_i_can_complete is True:
            process_instance_query = process_instance_query.filter(
                ProcessInstanceModel.process_initiator_id != user.id
            )
            process_instance_query = process_instance_query.join(
                HumanTaskModel,
                and_(
                    HumanTaskModel.process_instance_id == ProcessInstanceModel.id,
                    HumanTaskModel.lane_assignment_id.is_(None),  # type: ignore
                ),
            ).join(
                HumanTaskUserModel,
                and_(HumanTaskUserModel.human_task_id == HumanTaskModel.id, HumanTaskUserModel.user_id == user.id),
            )
            if has_active_status:
                process_instance_query = process_instance_query.filter(
                    HumanTaskModel.completed.is_(False)  # type: ignore
                )

        if with_tasks_assigned_to_my_group is True:
            group_model_join_conditions = [GroupModel.id == HumanTaskModel.lane_assignment_id]
            if user_group_identifier:
                group_model_join_conditions.append(GroupModel.identifier == user_group_identifier)

            process_instance_query = process_instance_query.join(HumanTaskModel)
            if has_active_status:
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
        report_column_list = cls.get_filter_value(filters, 'report_column_list')
        report_filter_by_list = cls.get_filter_value(filters, 'report_filter_by_list')
        stock_columns = cls.get_column_names_for_model(ProcessInstanceModel)
        if isinstance(report_column_list, list):
            process_instance_report.report_metadata["columns"] = report_column_list
        if isinstance(report_filter_by_list, list):
            process_instance_report.report_metadata["filter_by"] = report_filter_by_list

        for column in process_instance_report.report_metadata["columns"]:
            if column["accessor"] in stock_columns:
                continue
            instance_metadata_alias = aliased(ProcessInstanceMetadataModel)
            instance_metadata_aliases[column["accessor"]] = instance_metadata_alias

            filter_for_column = None
            if "filter_by" in process_instance_report.report_metadata:
                filter_for_column = next(
                    (
                        f
                        for f in process_instance_report.report_metadata["filter_by"]
                        if f["field_name"] == column["accessor"]
                    ),
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
        order_by_array = process_instance_report.report_metadata["order_by"]
        if len(order_by_array) < 1:
            order_by_array = ProcessInstanceReportModel.default_order_by()
        for order_by_option in order_by_array:
            attribute = re.sub("^-", "", order_by_option)
            if attribute in stock_columns:
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
        results = cls.add_metadata_columns_to_process_instance(
            process_instances.items, process_instance_report.report_metadata["columns"]
        )

        for value in cls.check_filter_value(filters, 'oldest_open_human_task_fields'):
            results = cls.add_human_task_fields(results, value)
        response_json = {
            "report": process_instance_report,
            "results": results,
            "filters": filters,
            "hash": "HEY",
            "pagination": {
                "count": len(results),
                "total": process_instances.total,
                "pages": process_instances.pages,
            },
        }
        return response_json
