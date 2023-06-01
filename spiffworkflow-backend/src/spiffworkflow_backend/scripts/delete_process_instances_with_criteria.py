from time import time
from typing import Any

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script
from sqlalchemy import or_


class DeleteProcessInstancesWithCriteria(Script):
    def get_description(self) -> str:
        return "Delete process instances that match the provided criteria,"

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        criteria_list = args[0]

        delete_criteria = []
        delete_time = time()

        for criteria in criteria_list:
            delete_criteria.append(
                (ProcessInstanceModel.process_model_identifier == criteria["name"])
                & ProcessInstanceModel.status.in_(criteria["status"])  # type: ignore
                & (ProcessInstanceModel.updated_at_in_seconds < (delete_time - criteria["last_updated_delta"]))
            )

        results = ProcessInstanceModel.query.filter(or_(*delete_criteria)).limit(100).all()
        rows_affected = len(results)

        if rows_affected > 0:
            for deletion in results:
                db.session.delete(deletion)
            db.session.commit()

        return rows_affected
