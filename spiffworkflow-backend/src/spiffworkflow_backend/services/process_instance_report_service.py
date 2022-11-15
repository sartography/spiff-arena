"""process_instance_report_service."""
from dataclasses import dataclass
from typing import Optional

from spiffworkflow_backend.models.process_instance_report import (
    ProcessInstanceReportModel,
)


@dataclass
class ProcessInstanceReportFilter:
    """ProcessInstanceReportFilter."""

    process_model_identifier: Optional[str] = None
    start_from: Optional[int] = None
    start_to: Optional[int] = None
    end_from: Optional[int] = None
    end_to: Optional[int] = None
    process_status: Optional[list[str]] = None


class ProcessInstanceReportService:
    """ProcessInstanceReportService."""
    @classmethod
    def filter_by_to_dict(
        cls, process_instance_report: ProcessInstanceReportModel
    ) -> dict[str,str]:
        metadata = process_instance_report.report_metadata
        filter_by = metadata.get("filter_by", [])
        filters = {d["field_name"]: d["field_value"] for d in filter_by if "field_name" in d and "field_value" in d}
        return filters

    @classmethod
    def filter_from_metadata(
        cls, process_instance_report: ProcessInstanceReportModel
    ) -> ProcessInstanceReportFilter:
        """Filter_from_metadata."""
        filters = cls.filter_by_to_dict(process_instance_report)

        def int_value(key: str) -> Optional[int]:
            return int(filters[key]) if key in filters else None

        def list_value(key: str) -> Optional[list[str]]:
            return filters[key].split(",") if key in filters else None

        process_model_identifier = filters.get("process_model_identifier")
        start_from = int_value("start_from")
        start_to = int_value("start_to")
        end_from = int_value("end_from")
        end_to = int_value("end_to")
        process_status = list_value("process_status")

        process_instance_report_filter = ProcessInstanceReportFilter(
            process_model_identifier,
            start_from,
            start_to,
            end_from,
            end_to,
            process_status,
        )

        return process_instance_report_filter
