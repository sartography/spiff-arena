from sqlalchemy import or_

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_caller import ProcessCallerCacheModel
from spiffworkflow_backend.models.process_caller_relationship import ProcessCallerRelationshipModel
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel


class CalledProcessNotFoundError(Exception):
    pass


class CallingProcessNotFoundError(Exception):
    pass


# TODO: delete this file
class ProcessCallerService:
    @staticmethod
    def count() -> int:
        return ProcessCallerRelationshipModel.query.count()  # type: ignore

    @staticmethod
    def clear_cache() -> None:
        db.session.query(ProcessCallerRelationshipModel).delete()

    @staticmethod
    def clear_cache_for_process_ids(reference_cache_ids: list[int]) -> None:
        db.session.query(ProcessCallerCacheModel).filter(
            or_(
                ProcessCallerRelationshipModel.called_reference_cache_process_id.in_(reference_cache_ids),
                ProcessCallerRelationshipModel.calling_reference_cache_process_id.in_(reference_cache_ids),
            )
        ).delete()

    @staticmethod
    def add_caller(process_id: str, called_process_ids: list[str]) -> None:
        reference_cache_records = (
            ReferenceCacheModel.basic_query()
            .filter(ReferenceCacheModel.identifier.in_(called_process_ids + [process_id]))  # type: ignore
            .all()
        )
        reference_cache_dict = {r.identifier: r.id for r in reference_cache_records}
        for called_process_id in called_process_ids:
            if called_process_id not in reference_cache_dict:
                raise CallingProcessNotFoundError(
                    f"Could not find calling process id '{called_process_id}' in reference_cache table."
                )
            if process_id not in reference_cache_dict:
                raise CalledProcessNotFoundError(
                    f"Could not find called process id '{called_process_id}' in reference_cache table."
                )
            ProcessCallerRelationshipModel.insert_or_update(
                called_reference_cache_process_id=reference_cache_dict[called_process_id],
                calling_reference_cache_process_id=reference_cache_dict[process_id],
            )

    @staticmethod
    def callers(process_ids: list[str]) -> list[str]:
        records = (
            db.session.query(ProcessCallerCacheModel).filter(ProcessCallerCacheModel.process_identifier.in_(process_ids)).all()
        )
        return sorted({r.calling_process_identifier for r in records})
