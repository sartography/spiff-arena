
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.spec_reference import SpecReference
from spiffworkflow_backend.models.process_caller import ProcessCallerCache

class ProcessCallerService:

    @staticmethod
    def count() -> int:
        return ProcessCallerCache.query.count()
    
    @staticmethod
    def clear_cache() -> None:
        db.session.query(ProcessCallerCache).delete()

    @staticmethod
    def clear_cache_for_process_ids(process_ids: list[str]) -> None:
        db.session.query(ProcessCallerCache).filter(ProcessCallerCache.process_identifier.in_(process_ids)).delete()
