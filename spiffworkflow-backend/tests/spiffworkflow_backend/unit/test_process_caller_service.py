import pytest
from flask.app import Flask
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_caller import ProcessCallerCache
from spiffworkflow_backend.services.process_caller_service import ProcessCallerService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

@pytest.fixture()
def with_clean_cache(app: Flask) -> None:
    db.session.query(ProcessCallerCache).delete()
    db.session.commit()
    yield

@pytest.fixture()
def with_no_process_callers(with_clean_cache: None) -> None:
    yield

@pytest.fixture()
def with_single_process_caller(with_clean_cache: None) -> None:
    db.session.add(ProcessCallerCache(process_identifier="called_once", calling_process_identifier="one_caller"))
    db.session.commit()
    yield

@pytest.fixture()
def with_multiple_process_callers(with_clean_cache: None) -> None:
    db.session.add(ProcessCallerCache(process_identifier="called_many", calling_process_identifier="caller1"))
    db.session.add(ProcessCallerCache(process_identifier="called_many", calling_process_identifier="caller2"))
    db.session.add(ProcessCallerCache(process_identifier="called_many", calling_process_identifier="caller3"))
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

    def test_can_clear_the_cache_for_process_id_and_leave_other_process_ids_alone(self,
                                                                                  with_single_process_caller: None,
                                                                                  with_multiple_process_callers: None,
                                                                                  ) -> None:
        ProcessCallerService.clear_cache_for_process_ids(["called_many"])
        assert ProcessCallerService.count() == 1

    def test_can_clear_the_cache_for_process_id_when_it_doesnt_exist(
            self,
            with_no_process_callers: None,
    ) -> None:
        assert ProcessCallerService.count() == 0
