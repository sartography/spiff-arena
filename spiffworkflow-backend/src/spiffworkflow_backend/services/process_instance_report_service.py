"""Process_instance_report_service."""
from dataclasses import dataclass
from typing import Optional

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

        return d


class ProcessInstanceReportService:
    """ProcessInstanceReportService."""

    @classmethod
    def report_with_identifier(
        cls, user: UserModel, report_identifier: Optional[str] = None
    ) -> ProcessInstanceReportModel:
        """Report_with_filter."""
        if report_identifier is None:
            return ProcessInstanceReportModel.default_report(user)

        # TODO replace with system reports that are loaded on launch (or similar)
        temp_system_metadata_map = {
            "system_report_instances_initiated_by_me": {
                "columns": [
                    {
                        "Header": "process_model_identifier",
                        "accessor": "process_model_identifier",
                    },
                    {"Header": "start_in_seconds", "accessor": "start_in_seconds"},
                    {"Header": "id", "accessor": "id"},
                    {"Header": "end_in_seconds", "accessor": "end_in_seconds"},
                    {"Header": "status", "accessor": "status"},
                ],
            },
            "system_report_instances_with_tasks_completed_by_me": {
                "columns": [
                    {"Header": "start_in_seconds", "accessor": "start_in_seconds"},
                    {"Header": "end_in_seconds", "accessor": "end_in_seconds"},
                    {"Header": "status", "accessor": "status"},
                    {"Header": "id", "accessor": "id"},
                    {
                        "Header": "process_model_identifier",
                        "accessor": "process_model_identifier",
                    },
                ],
            },
            "system_report_instances_with_tasks_completed_by_my_groups": {
                "columns": [
                    {
                        "Header": "process_model_identifier",
                        "accessor": "process_model_identifier",
                    },
                    {"Header": "start_in_seconds", "accessor": "start_in_seconds"},
                    {"Header": "end_in_seconds", "accessor": "end_in_seconds"},
                    {"Header": "status", "accessor": "status"},
                    {"Header": "id", "accessor": "id"},
                ],
            },
        }

        process_instance_report = ProcessInstanceReportModel(
            identifier=report_identifier,
            created_by_id=user.id,
            report_metadata=temp_system_metadata_map[report_identifier],
        )

        return process_instance_report

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

        report_filter = ProcessInstanceReportFilter(
            process_model_identifier,
            start_from,
            start_to,
            end_from,
            end_to,
            process_status,
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

        return report_filter
