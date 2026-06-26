from collections import Counter
from time import time
from typing import Any

from sqlalchemy import or_

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


class DeleteProcessInstancesWithCriteria(Script):
    DEFAULT_LIMIT = 100

    def get_description(self) -> str:
        return "Delete process instances that match the provided criteria,"

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if not args:
            raise ValueError("criteria list is required")

        criteria_list = args[0]
        limit = self._limit_from_args(args, kwargs)
        return_summary = bool(kwargs.get("return_summary", False))

        delete_criteria = []
        delete_time = time()

        for criteria in criteria_list:
            delete_criteria.append(self._get_criteria_for_delete(criteria, delete_time))

        if not delete_criteria:
            if return_summary:
                return {"total_deleted": 0, "limit": limit, "criteria_count": 0, "by_model_status": []}
            return 0

        results = ProcessInstanceModel.query.filter(or_(*delete_criteria)).limit(limit).all()
        rows_affected = len(results)
        summary = {
            "total_deleted": rows_affected,
            "limit": limit,
            "criteria_count": len(criteria_list),
            "by_model_status": self._grouped_summary(results),
        }

        if rows_affected > 0:
            for deletion in results:
                db.session.delete(deletion)
            db.session.commit()

        if return_summary:
            return summary

        return rows_affected

    def _limit_from_args(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> int:
        limit = kwargs.get("limit", args[1] if len(args) > 1 else self.__class__.DEFAULT_LIMIT)
        limit = int(limit)
        if limit < 1:
            raise ValueError("limit must be greater than zero")
        return limit

    def _grouped_summary(self, results: list[ProcessInstanceModel]) -> list[dict[str, Any]]:
        counts = Counter((result.process_model_identifier, result.status) for result in results)
        return [
            {
                "process_model_identifier": process_model_identifier,
                "status": status,
                "deleted": deleted,
            }
            for (process_model_identifier, status), deleted in sorted(counts.items())
        ]

    def _get_criteria_for_delete(self, criteria: dict[str, Any], delete_time: float) -> Any:
        criterion = ProcessInstanceModel.status.in_(criteria["status"]) & (  # type: ignore[attr-defined]
            ProcessInstanceModel.updated_at_in_seconds < (delete_time - criteria["last_updated_delta"])
        )

        if criteria.get("name"):
            criterion = criterion & (ProcessInstanceModel.process_model_identifier == criteria["name"])

        if criteria.get("exclude_names"):
            criterion = criterion & ~ProcessInstanceModel.process_model_identifier.in_(criteria["exclude_names"])  # type: ignore[attr-defined]

        for prefix in criteria.get("exclude_name_prefixes", []):
            criterion = criterion & ProcessInstanceModel.process_model_identifier.notlike(f"{prefix}%")  # type: ignore[attr-defined]

        return criterion
