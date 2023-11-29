from collections.abc import Generator

import pytest
from flask.app import Flask
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_caller import ProcessCallerCacheModel
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
    db.session.add(ProcessCallerCacheModel(process_identifier="called_once", calling_process_identifier="one_caller"))
    db.session.commit()
    yield


@pytest.fixture()
def with_multiple_process_callers(with_clean_cache: None) -> Generator[None, None, None]:
    db.session.add(ProcessCallerCacheModel(process_identifier="called_many", calling_process_identifier="one_caller"))
    db.session.add(ProcessCallerCacheModel(process_identifier="called_many", calling_process_identifier="two_caller"))
    db.session.add(ProcessCallerCacheModel(process_identifier="called_many", calling_process_identifier="three_caller"))
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
        ProcessCallerService.clear_cache_for_process_ids(["called_once"])
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
