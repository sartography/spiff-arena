from sqlalchemy import or_

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_caller_relationship import CalledProcessNotFoundError
from spiffworkflow_backend.models.process_caller_relationship import CallingProcessNotFoundError
from spiffworkflow_backend.models.process_caller_relationship import ProcessCallerRelationshipModel
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel


# TODO: delete this file
class ProcessCallerService:
    @staticmethod
    def count() -> int:
        """This is used in tests ONLY."""
        return ProcessCallerRelationshipModel.query.count()  # type: ignore

    @staticmethod
    def clear_cache() -> None:
        db.session.query(ProcessCallerRelationshipModel).delete()

    @staticmethod
    def clear_cache_for_process_ids(reference_cache_ids: list[int]) -> None:
        if len(reference_cache_ids) > 0:
            # query-invoked autoflush happens here
            ProcessCallerRelationshipModel.query.filter(
                or_(
                    ProcessCallerRelationshipModel.called_reference_cache_process_id.in_(reference_cache_ids),
                    ProcessCallerRelationshipModel.calling_reference_cache_process_id.in_(reference_cache_ids),
                )
            ).delete()

    @staticmethod
    def add_caller(calling_process_identifier: str, called_process_identifiers: list[str]) -> None:
        reference_cache_records = (
            ReferenceCacheModel.basic_query()
            .filter(ReferenceCacheModel.identifier.in_(called_process_identifiers + [calling_process_identifier]))  # type: ignore
            .all()
        )
        reference_cache_dict = {r.identifier: r.id for r in reference_cache_records}
        if calling_process_identifier not in reference_cache_dict:
            raise CallingProcessNotFoundError(
                f"Could not find calling process id '{calling_process_identifier}' in reference_cache table."
            )
        for called_process_identifier in called_process_identifiers:
            if called_process_identifier not in reference_cache_dict:
                raise CalledProcessNotFoundError(
                    f"Could not find called process id '{called_process_identifier}' in reference_cache table."
                )
            ProcessCallerRelationshipModel.insert_or_update(
                called_reference_cache_process_id=reference_cache_dict[called_process_identifier],
                calling_reference_cache_process_id=reference_cache_dict[calling_process_identifier],
            )
