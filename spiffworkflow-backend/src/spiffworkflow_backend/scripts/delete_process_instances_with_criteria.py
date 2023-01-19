"""Delete_process_instances_with_criteria."""
from time import time
from typing import Any

from sqlalchemy import or_

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.models.spiff_step_details import SpiffStepDetailsModel
from spiffworkflow_backend.scripts.script import Script


class DeleteProcessInstancesWithCriteria(Script):
    """DeleteProcessInstancesWithCriteria."""

    def get_description(self) -> str:
        """Get_description."""
        return "Delete process instances that match the provided criteria,"

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Run."""
        criteria_list = args[0]

        delete_criteria = []
        delete_time = time()

        for criteria in criteria_list:
            delete_criteria.append(
                (ProcessInstanceModel.process_model_identifier == criteria["name"])
                & ProcessInstanceModel.status.in_(criteria["status"])  # type: ignore
                & (
                    ProcessInstanceModel.updated_at_in_seconds
                    < (delete_time - criteria["last_updated_delta"])
                )
            )

        results = (
            ProcessInstanceModel.query.filter(or_(*delete_criteria)).limit(100).all()
        )
        rows_affected = len(results)

        if rows_affected > 0:
            ids_to_delete = list(map(lambda r: r.id, results))  # type: ignore

            step_details = SpiffStepDetailsModel.query.filter(
                SpiffStepDetailsModel.process_instance_id.in_(ids_to_delete)  # type: ignore
            ).all()

            for deletion in step_details:
                db.session.delete(deletion)
            for deletion in results:
                db.session.delete(deletion)
            db.session.commit()

        return rows_affected
