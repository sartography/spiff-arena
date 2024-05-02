from sqlalchemy import insert

from spiffworkflow_backend.models.cache_generation import CacheGenerationModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.services.upsearch_service import UpsearchService


class ReferenceCacheService:
    @classmethod
    def add_unique_reference_cache_object(
        cls, reference_objects: dict[str, ReferenceCacheModel], reference_cache: ReferenceCacheModel
    ) -> None:
        reference_cache_unique = f"{reference_cache.identifier}{reference_cache.relative_location}{reference_cache.type}"
        reference_objects[reference_cache_unique] = reference_cache

    @classmethod
    def add_new_generation(cls, reference_objects: dict[str, ReferenceCacheModel]) -> None:
        # get inserted autoincrement primary key value back in a database agnostic way without committing the db session
        ins = insert(CacheGenerationModel).values(cache_table="reference_cache")  # type: ignore
        res = db.session.execute(ins)
        cache_generation_id = res.inserted_primary_key[0]

        # add primary key value to each element in reference objects list and store in new list
        reference_object_list_with_cache_generation_id = []
        for reference_object in reference_objects.values():
            reference_object.generation_id = cache_generation_id
            reference_object_list_with_cache_generation_id.append(reference_object)

        db.session.bulk_save_objects(reference_object_list_with_cache_generation_id)
        db.session.commit()

    @classmethod
    def upsearch(cls, location: str, identifier: str, type: str) -> str | None:
        locations = UpsearchService.upsearch_locations(location)
        references = (
            ReferenceCacheModel.basic_query()
            .filter_by(
                identifier=identifier,
                type=type,
            )
            .filter(ReferenceCacheModel.relative_location.in_(locations))  # type: ignore
            .order_by(ReferenceCacheModel.relative_location.desc())  # type: ignore
            .all()
        )

        for reference in references:
            # TODO: permissions check
            return reference.relative_location  # type: ignore

        return None
