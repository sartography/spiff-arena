from dataclasses import dataclass
from typing import Optional

from spiffworkflow_backend.models.process_instance_report import ProcessInstanceReportModel

@dataclass
class ProcessInstanceReportFilter:
    process_model_identifier: Optional[str] = None
    start_from: Optional[int] = None
    start_to: Optional[int] = None
    end_from: Optional[int] = None
    end_to: Optional[int] = None
    process_status: Optional[list[str]] = None

class ProcessInstanceReportService:
    """ProcessInstanceReportService."""
    @classmethod
    def filter_from_metadata(cls, process_instance_report: ProcessInstanceReportModel) -> ProcessInstanceReportFilter:
        process_model_identifier: Optional[str] = None
        start_from: Optional[int] = None
        start_to: Optional[int] = None
        end_from: Optional[int] = None
        end_to: Optional[int] = None
        process_status: Optional[list[str]] = None

        metadata = process_instance_report.report_metadata
        if "filter_by" in metadata:
            pass

        process_instance_report_filter = ProcessInstanceReportFilter(
            process_model_identifier,
            start_from,
            start_to,
            end_from,
            end_to,
            process_status,
        )
        
        return process_instance_report_filter

    #def passes_filter(
    #    self, process_instance_dict: dict, substitution_variables: dict
    #) -> bool:
    #    """Passes_filter."""
    #    if "filter_by" in self.report_metadata:
    #        for filter_by in self.report_metadata["filter_by"]:
    #            field_name = filter_by["field_name"]
    #            operator = filter_by["operator"]
    #            field_value = self.with_substitutions(
    #                filter_by["field_value"], substitution_variables
    #            )
    #            if operator == "equals":
    ##                if str(process_instance_dict.get(field_name)) != str(field_value):
    #                    return False
    #
    #    return True
