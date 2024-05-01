from collections.abc import Generator

import pytest
from flask.app import Flask
from spiffworkflow_backend.models.cache_generation import CacheGenerationModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_caller import ProcessCallerCacheModel
from spiffworkflow_backend.models.process_caller_relationship import ProcessCallerRelationshipModel
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.services.process_caller_service import ProcessCallerService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


@pytest.fixture()
def with_clean_cache(app: Flask) -> Generator[None, None, None]:
    db.session.query(ProcessCallerCacheModel).delete()
    db.session.commit()
    yield


@pytest.fixture()
def with_no_process_callers(with_clean_cache: None) -> Generator[None, None, None]:
    yield


@pytest.fixture()
def with_single_process_caller(with_clean_cache: None) -> Generator[None, None, None]:
    cache_generation = CacheGenerationModel(cache_table="reference_cache")
    db.session.add(cache_generation)
    db.session.commit()
    called_cache = ReferenceCacheModel.from_params(
        identifier="called_once",
        type="process",
        display_name="called_once",
        file_name="called_once",
        relative_location="called_once",
        use_current_cache_generation=True,
    )
    calling_cache = ReferenceCacheModel.from_params(
        identifier="calling_cache",
        type="process",
        display_name="calling_cache",
        file_name="calling_cache",
        relative_location="calling_cache",
        use_current_cache_generation=True,
    )
    db.session.add(called_cache)
    db.session.add(calling_cache)
    db.session.commit()
    caller_relationship = ProcessCallerRelationshipModel(
        called_reference_cache_process_id=called_cache.id, calling_reference_cache_process_id=calling_cache.id
    )
    db.session.add(caller_relationship)
    db.session.commit()
    yield


@pytest.fixture()
def with_multiple_process_callers(with_clean_cache: None) -> Generator[None, None, None]:
    called_cache = ReferenceCacheModel(identifier="called_many", type="process")
    calling_cache_one = ReferenceCacheModel(identifier="one_caller", type="process")
    calling_cache_two = ReferenceCacheModel(identifier="two_caller", type="process")
    calling_cache_three = ReferenceCacheModel(identifier="three_caller", type="process")
    db.session.add(called_cache)
    db.session.add(calling_cache_one)
    db.session.add(calling_cache_two)
    db.session.add(calling_cache_three)
    db.session.commit()
    db.session.add(
        ProcessCallerRelationshipModel(
            called_reference_cache_process_id=called_cache.id, calling_reference_cache_process_id=calling_cache_one.id
        )
    )
    db.session.add(
        ProcessCallerRelationshipModel(
            called_reference_cache_process_id=called_cache.id, calling_reference_cache_process_id=calling_cache_two.id
        )
    )
    db.session.add(
        ProcessCallerRelationshipModel(
            called_reference_cache_process_id=called_cache.id, calling_reference_cache_process_id=calling_cache_three.id
        )
    )
    db.session.commit()
    yield


class TestProcessCallerService(BaseTest):
    """Infer from class name."""

    def test_has_zero_count_when_empty(self, with_no_process_callers: None) -> None:
        assert ProcessCallerService.count() == 0

    def test_has_expected_count_when_not_empty(self, with_multiple_process_callers: None) -> None:
        assert ProcessCallerService.count() == 3

    def test_can_clear_the_cache(self, with_multiple_process_callers: None) -> None:
        ProcessCallerService.clear_cache()
        assert ProcessCallerService.count() == 0

    def test_can_clear_the_cache_when_empty(self, with_no_process_callers: None) -> None:
        ProcessCallerService.clear_cache()
        assert ProcessCallerService.count() == 0

    def test_can_clear_the_cache_for_process_id(self, with_single_process_caller: None) -> None:
        reference_cache = ReferenceCacheModel.query.filter_by(identifier="called_once").first()
        assert reference_cache is not None
        ProcessCallerService.clear_cache_for_process_ids([reference_cache.id])
        assert ProcessCallerService.count() == 0

    def test_can_clear_the_cache_for_calling_process_id(self, with_multiple_process_callers: None) -> None:
        ProcessCallerService.clear_cache_for_process_ids(["one_caller"])
        assert ProcessCallerService.count() == 2

    def test_can_clear_the_cache_for_callee_caller_process_id(
        self, with_single_process_caller: None, with_multiple_process_callers: None
    ) -> None:
        ProcessCallerService.clear_cache_for_process_ids(["one_caller"])
        assert ProcessCallerService.count() == 2

    def test_can_clear_the_cache_for_process_id_and_leave_other_process_ids_alone(
        self,
        with_single_process_caller: None,
        with_multiple_process_callers: None,
    ) -> None:
        ProcessCallerService.clear_cache_for_process_ids(["called_many"])
        assert ProcessCallerService.count() == 1

    def test_can_clear_the_cache_for_process_id_when_it_doesnt_exist(
        self,
        with_multiple_process_callers: None,
    ) -> None:
        ProcessCallerService.clear_cache_for_process_ids(["garbage"])
        assert ProcessCallerService.count() == 3

    def test_no_records_added_if_calling_process_ids_is_empty(self, with_no_process_callers: None) -> None:
        ProcessCallerService.add_caller("bob", [])
        assert ProcessCallerService.count() == 0

    def test_can_add_caller_for_new_process(self, with_no_process_callers: None) -> None:
        ProcessCallerService.add_caller("bob", ["new_caller"])
        assert ProcessCallerService.count() == 1

    def test_can_many_callers_for_new_process(self, with_no_process_callers: None) -> None:
        ProcessCallerService.add_caller("bob", ["new_caller", "another_new_caller"])
        assert ProcessCallerService.count() == 2

    def test_can_add_caller_for_existing_process(self, with_multiple_process_callers: None) -> None:
        ProcessCallerService.add_caller("called_many", ["new_caller"])
        assert ProcessCallerService.count() == 4

    def test_can_add_many_callers_for_existing_process(self, with_multiple_process_callers: None) -> None:
        ProcessCallerService.add_caller("called_many", ["new_caller", "another_new_caller"])
        assert ProcessCallerService.count() == 5

    def test_can_track_duplicate_callers(self, with_no_process_callers: None) -> None:
        ProcessCallerService.add_caller("bob", ["new_caller", "new_caller"])
        assert ProcessCallerService.count() == 2

    def test_can_return_no_callers_when_no_records(self, with_no_process_callers: None) -> None:
        assert ProcessCallerService.callers(["bob"]) == []

    def test_can_return_no_callers_when_process_id_is_unknown(self, with_multiple_process_callers: None) -> None:
        assert ProcessCallerService.callers(["bob"]) == []

    def test_can_return_single_caller(self, with_single_process_caller: None) -> None:
        assert ProcessCallerService.callers(["called_once"]) == ["one_caller"]

    def test_can_return_mulitple_callers(self, with_multiple_process_callers: None) -> None:
        callers = sorted(ProcessCallerService.callers(["called_many"]))
        assert callers == ["one_caller", "three_caller", "two_caller"]

    def test_can_return_single_caller_when_there_are_other_process_ids(
        self, with_single_process_caller: None, with_multiple_process_callers: None
    ) -> None:
        assert ProcessCallerService.callers(["called_once"]) == ["one_caller"]
