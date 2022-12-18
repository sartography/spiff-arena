"""Process_instance_report_service."""
from dataclasses import dataclass
from typing import Optional

import sqlalchemy
from flask_bpmn.models.db import db

from spiffworkflow_backend.models.process_instance_report import (
    ProcessInstanceReportModel,
)
from spiffworkflow_backend.models.user import UserModel


@dataclass
class ProcessInstanceReportFilter:
    """ProcessInstanceReportFilter."""

    process_model_identifier: Optional[str] = None
    start_from: Optional[int] = None
    start_to: Optional[int] = None
    end_from: Optional[int] = None
    end_to: Optional[int] = None
    process_status: Optional[list[str]] = None
    initiated_by_me: Optional[bool] = None
    with_tasks_completed_by_me: Optional[bool] = None
    with_tasks_completed_by_my_group: Optional[bool] = None
    with_relation_to_me: Optional[bool] = None

    def to_dict(self) -> dict[str, str]:
        """To_dict."""
        d = {}

        if self.process_model_identifier is not None:
            d["process_model_identifier"] = self.process_model_identifier
        if self.start_from is not None:
            d["start_from"] = str(self.start_from)
        if self.start_to is not None:
            d["start_to"] = str(self.start_to)
        if self.end_from is not None:
            d["end_from"] = str(self.end_from)
        if self.end_to is not None:
            d["end_to"] = str(self.end_to)
        if self.process_status is not None:
            d["process_status"] = ",".join(self.process_status)
        if self.initiated_by_me is not None:
            d["initiated_by_me"] = str(self.initiated_by_me).lower()
        if self.with_tasks_completed_by_me is not None:
            d["with_tasks_completed_by_me"] = str(
                self.with_tasks_completed_by_me
            ).lower()
        if self.with_tasks_completed_by_my_group is not None:
            d["with_tasks_completed_by_my_group"] = str(
                self.with_tasks_completed_by_my_group
            ).lower()
        if self.with_relation_to_me is not None:
            d["with_relation_to_me"] = str(self.with_relation_to_me).lower()

        return d


class ProcessInstanceReportService:
    """ProcessInstanceReportService."""

    @classmethod
    def report_with_identifier(
        cls,
        user: UserModel,
        report_id: Optional[int] = None,
        report_identifier: Optional[str] = None,
    ) -> ProcessInstanceReportModel:
        """Report_with_filter."""
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

        # TODO replace with system reports that are loaded on launch (or similar)
        temp_system_metadata_map = {
            "default": {
                "columns": cls.builtin_column_options(),
                "filter_by": [],
                "order_by": ["-start_in_seconds", "-id"],
            },
            "system_report_instances_initiated_by_me": {
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
                "filter_by": [{"field_name": "initiated_by_me", "field_value": True}],
                "order_by": ["-start_in_seconds", "-id"],
            },
            "system_report_instances_with_tasks_completed_by_me": {
                "columns": cls.builtin_column_options(),
                "filter_by": [
                    {"field_name": "with_tasks_completed_by_me", "field_value": True}
                ],
                "order_by": ["-start_in_seconds", "-id"],
            },
            "system_report_instances_with_tasks_completed_by_my_groups": {
                "columns": cls.builtin_column_options(),
                "filter_by": [
                    {
                        "field_name": "with_tasks_completed_by_my_group",
                        "field_value": True,
                    }
                ],
                "order_by": ["-start_in_seconds", "-id"],
            },
        }

        process_instance_report = ProcessInstanceReportModel(
            identifier=report_identifier,
            created_by_id=user.id,
            report_metadata=temp_system_metadata_map[report_identifier],
        )

        return process_instance_report  # type: ignore

    @classmethod
    def filter_by_to_dict(
        cls, process_instance_report: ProcessInstanceReportModel
    ) -> dict[str, str]:
        """Filter_by_to_dict."""
        metadata = process_instance_report.report_metadata
        filter_by = metadata.get("filter_by", [])
        filters = {
            d["field_name"]: d["field_value"]
            for d in filter_by
            if "field_name" in d and "field_value" in d
        }
        return filters

    @classmethod
    def filter_from_metadata(
        cls, process_instance_report: ProcessInstanceReportModel
    ) -> ProcessInstanceReportFilter:
        """Filter_from_metadata."""
        filters = cls.filter_by_to_dict(process_instance_report)

        def bool_value(key: str) -> Optional[bool]:
            """Bool_value."""
            return bool(filters[key]) if key in filters else None

        def int_value(key: str) -> Optional[int]:
            """Int_value."""
            return int(filters[key]) if key in filters else None

        def list_value(key: str) -> Optional[list[str]]:
            """List_value."""
            return filters[key].split(",") if key in filters else None

        process_model_identifier = filters.get("process_model_identifier")
        start_from = int_value("start_from")
        start_to = int_value("start_to")
        end_from = int_value("end_from")
        end_to = int_value("end_to")
        process_status = list_value("process_status")
        initiated_by_me = bool_value("initiated_by_me")
        with_tasks_completed_by_me = bool_value("with_tasks_completed_by_me")
        with_tasks_completed_by_my_group = bool_value(
            "with_tasks_completed_by_my_group"
        )
        with_relation_to_me = bool_value("with_relation_to_me")

        report_filter = ProcessInstanceReportFilter(
            process_model_identifier,
            start_from,
            start_to,
            end_from,
            end_to,
            process_status,
            initiated_by_me,
            with_tasks_completed_by_me,
            with_tasks_completed_by_my_group,
            with_relation_to_me,
        )

        return report_filter

    @classmethod
    def filter_from_metadata_with_overrides(
        cls,
        process_instance_report: ProcessInstanceReportModel,
        process_model_identifier: Optional[str] = None,
        start_from: Optional[int] = None,
        start_to: Optional[int] = None,
        end_from: Optional[int] = None,
        end_to: Optional[int] = None,
        process_status: Optional[str] = None,
        initiated_by_me: Optional[bool] = None,
        with_tasks_completed_by_me: Optional[bool] = None,
        with_tasks_completed_by_my_group: Optional[bool] = None,
        with_relation_to_me: Optional[bool] = None,
    ) -> ProcessInstanceReportFilter:
        """Filter_from_metadata_with_overrides."""
        report_filter = cls.filter_from_metadata(process_instance_report)

        if process_model_identifier is not None:
            report_filter.process_model_identifier = process_model_identifier
        if start_from is not None:
            report_filter.start_from = start_from
        if start_to is not None:
            report_filter.start_to = start_to
        if end_from is not None:
            report_filter.end_from = end_from
        if end_to is not None:
            report_filter.end_to = end_to
        if process_status is not None:
            report_filter.process_status = process_status.split(",")
        if initiated_by_me is not None:
            report_filter.initiated_by_me = initiated_by_me
        if with_tasks_completed_by_me is not None:
            report_filter.with_tasks_completed_by_me = with_tasks_completed_by_me
        if with_tasks_completed_by_my_group is not None:
            report_filter.with_tasks_completed_by_my_group = (
                with_tasks_completed_by_my_group
            )
        if with_relation_to_me is not None:
            report_filter.with_relation_to_me = with_relation_to_me

        return report_filter

    @classmethod
    def add_metadata_columns_to_process_instance(
        cls,
        process_instance_sqlalchemy_rows: list[sqlalchemy.engine.row.Row],  # type: ignore
        metadata_columns: list[dict],
    ) -> list[dict]:
        """Add_metadata_columns_to_process_instance."""
        results = []
        for process_instance in process_instance_sqlalchemy_rows:
            process_instance_dict = process_instance["ProcessInstanceModel"].serialized
            for metadata_column in metadata_columns:
                if metadata_column["accessor"] not in process_instance_dict:
                    process_instance_dict[
                        metadata_column["accessor"]
                    ] = process_instance[metadata_column["accessor"]]

            results.append(process_instance_dict)
        return results

    @classmethod
    def get_column_names_for_model(cls, model: db.Model) -> list[str]:  # type: ignore
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
            {"Header": "Username", "accessor": "username", "filterable": False},
            {"Header": "Status", "accessor": "status", "filterable": False},
        ]
