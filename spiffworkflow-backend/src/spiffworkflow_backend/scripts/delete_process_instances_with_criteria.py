from collections import Counter
from time import time
from typing import Any

from sqlalchemy import or_

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.kkv_data_store import KKVDataStoreModel
from spiffworkflow_backend.models.kkv_data_store_entry import KKVDataStoreEntryModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script

DEFAULT_LIMIT = 100


def _limit_from_args(args: tuple[Any, ...], kwargs: dict[str, Any]) -> int:
    limit = kwargs.get("limit", args[1] if len(args) > 1 else DEFAULT_LIMIT)
    limit = int(limit)
    if limit < 1:
        raise ValueError("limit must be greater than zero")
    return limit


def _grouped_summary(results: list[ProcessInstanceModel]) -> list[dict[str, Any]]:
    counts = Counter((result.process_model_identifier, result.status) for result in results)
    return [
        {
            "process_model_identifier": process_model_identifier,
            "status": status,
            "deleted": deleted,
        }
        for (process_model_identifier, status), deleted in sorted(counts.items())
    ]


def _delete_criterion(criteria: dict[str, Any], delete_time: float) -> Any:
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


def _process_group_identifier(process_model_identifier: str | None) -> str | None:
    if not process_model_identifier or "/" not in process_model_identifier:
        return None
    return process_model_identifier.rsplit("/", 1)[0]


def _write_run_log(
    script_attributes_context: ScriptAttributesContext,
    summary: dict[str, Any],
    kwargs: dict[str, Any],
) -> None:
    identifier = kwargs.get("run_log_data_store_identifier")
    run_key = kwargs.get("run_log_key")
    if not identifier or not run_key:
        return

    location = kwargs.get("run_log_location") or _process_group_identifier(script_attributes_context.process_model_identifier)
    store_model = db.session.query(KKVDataStoreModel).filter_by(identifier=identifier, location=location).first()
    if store_model is None:
        raise ValueError(f"Could not find KKV data store '{identifier}' at location '{location}'")

    secondary_key = kwargs.get("run_log_secondary_key", "summary")
    entry = (
        db.session.query(KKVDataStoreEntryModel)
        .filter_by(kkv_data_store_id=store_model.id, top_level_key=run_key, secondary_key=secondary_key)
        .first()
    )
    if entry is None:
        entry = KKVDataStoreEntryModel(
            kkv_data_store_id=store_model.id,
            top_level_key=run_key,
            secondary_key=secondary_key,
            value=summary,
        )
    else:
        entry.value = summary
    db.session.add(entry)
    db.session.commit()


class DeleteProcessInstancesWithCriteria(Script):
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
        limit = _limit_from_args(args, kwargs)
        return_summary = bool(kwargs.get("return_summary", False))

        delete_criteria = []
        delete_time = time()

        for criteria in criteria_list:
            delete_criteria.append(_delete_criterion(criteria, delete_time))

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
            "by_model_status": _grouped_summary(results),
        }

        if rows_affected > 0:
            for deletion in results:
                db.session.delete(deletion)
            db.session.commit()

        _write_run_log(script_attributes_context, summary, kwargs)

        if return_summary:
            return summary

        return rows_affected
