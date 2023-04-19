from sqlalchemy import or_
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.spec_reference import SpecReference
from spiffworkflow_backend.models.process_caller import ProcessCallerCache
from typing import List

class ProcessCallerService:

    @staticmethod
    def count() -> int:
        return ProcessCallerCache.query.count()
    
    @staticmethod
    def clear_cache() -> None:
        db.session.query(ProcessCallerCache).delete()

    @staticmethod
    def clear_cache_for_process_ids(process_ids: List[str]) -> None:
        db.session.query(ProcessCallerCache).filter(
            or_(
                ProcessCallerCache.process_identifier.in_(process_ids),
                ProcessCallerCache.calling_process_identifier.in_(process_ids),
            )
        ).delete()

    @staticmethod
    def add_callers(process_id: str, calling_process_ids: List[str]) -> None:
        for calling_process_id in calling_process_ids:
            db.session.add(ProcessCallerCache(process_identifier=process_id, calling_process_identifier=calling_process_id))
        db.session.commit()

    @staticmethod
    def callers(process_id: str) -> List[str]:
        records = db.session.query(ProcessCallerCache).filter(ProcessCallerCache.process_identifier==process_id).all()
        return list(map(lambda r: r.calling_process_identifier, records))
