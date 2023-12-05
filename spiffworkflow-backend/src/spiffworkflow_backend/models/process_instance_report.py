from __future__ import annotations

import sys
import typing
from dataclasses import dataclass
from typing import Any

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired
    from typing_extensions import TypedDict
else:
    from typing import NotRequired
    from typing import TypedDict

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.json_data import JsonDataModel  # noqa: F401
from spiffworkflow_backend.models.user import UserModel


class FilterValue(TypedDict):
    field_name: str
    field_value: str | int | bool
    operator: NotRequired[str]


class ReportMetadataColumn(TypedDict):
    Header: str
    accessor: str
    filterable: NotRequired[bool]


class ReportMetadata(TypedDict):
    columns: list[ReportMetadataColumn]
    filter_by: list[FilterValue]
    order_by: list[str]


class Report(TypedDict):
    id: int
    identifier: str
    name: str
    report_metadata: ReportMetadata


class ProcessInstanceReportAlreadyExistsError(Exception):
    pass


class ProcessInstanceReportResult(TypedDict):
    report_metadata: ReportMetadata
    results: list[dict]


# https://stackoverflow.com/a/56842689/6090676
class Reversor:
    def __init__(self, obj: Any):
        self.obj = obj

    def __eq__(self, other: Any) -> Any:
        return other.obj == self.obj

    def __lt__(self, other: Any) -> Any:
        return other.obj < self.obj


@dataclass
class ProcessInstanceReportModel(SpiffworkflowBaseDBModel):
    __tablename__ = "process_instance_report"
    __table_args__ = (
        db.UniqueConstraint(
            "created_by_id",
            "identifier",
            name="process_instance_report_unique",
        ),
    )

    id: int = db.Column(db.Integer, primary_key=True)
    identifier: str = db.Column(db.String(50), nullable=False, index=True)
    report_metadata: ReportMetadata = db.Column(db.JSON)
    created_by_id = db.Column(ForeignKey(UserModel.id), nullable=False, index=True)  # type: ignore
    created_by = relationship("UserModel")
    created_at_in_seconds = db.Column(db.Integer)
    updated_at_in_seconds = db.Column(db.Integer)

    json_data_hash: str = db.Column(db.String(255), nullable=False, index=True)

    def get_report_metadata(self) -> ReportMetadata:
        rdata_dict = JsonDataModel.find_data_dict_by_hash(self.json_data_hash)
        rdata = typing.cast(ReportMetadata, rdata_dict)
        return rdata

    @classmethod
    def default_order_by(cls) -> list[str]:
        return ["-start_in_seconds", "-id"]

    @classmethod
    def create_report(
        cls,
        identifier: str,
        user: UserModel,
        report_metadata: ReportMetadata,
    ) -> ProcessInstanceReportModel:
        process_instance_report = ProcessInstanceReportModel.query.filter_by(
            identifier=identifier,
            created_by_id=user.id,
        ).first()

        if process_instance_report is not None:
            raise ProcessInstanceReportAlreadyExistsError(f"Process instance report with identifier already exists: {identifier}")

        report_metadata_dict = typing.cast(dict[str, Any], report_metadata)
        json_data_hash = JsonDataModel.create_and_insert_json_data_from_dict(report_metadata_dict)

        process_instance_report = cls(
            identifier=identifier,
            created_by_id=user.id,
            report_metadata=report_metadata,
            json_data_hash=json_data_hash,
        )
        db.session.add(process_instance_report)
        db.session.commit()

        return process_instance_report  # type: ignore

    def with_substitutions(self, field_value: Any, substitution_variables: dict) -> Any:
        if substitution_variables is not None:
            for key, value in substitution_variables.items():
                if isinstance(value, str | int):
                    field_value = str(field_value).replace("{{" + key + "}}", str(value))
        return field_value
