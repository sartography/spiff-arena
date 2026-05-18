from collections.abc import Generator

import pytest
from flask.app import Flask

from spiffworkflow_backend.models.cache_generation import CacheGenerationModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_caller_relationship import CalledProcessNotFoundError
from spiffworkflow_backend.models.process_caller_relationship import CallingProcessNotFoundError
from spiffworkflow_backend.models.process_caller_relationship import ProcessCallerRelationshipModel
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.services.process_caller_service import ProcessCallerService
from spiffworkflow_backend.services.reference_cache_service import ReferenceCacheService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


@pytest.fixture()
def with_clean_cache(app: Flask) -> Generator[None, None, None]:
    ProcessCallerRelationshipModel.query.delete()
    db.session.commit()
    yield


@pytest.fixture()
def with_no_process_callers(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    request.getfixturevalue("with_clean_cache")
    yield


def create_reference_cache(identifier: str) -> ReferenceCacheModel:
    ref_cache = ReferenceCacheModel.from_params(
        identifier=identifier,
        type="process",
        display_name=identifier,
        file_name=identifier,
        relative_location=identifier,
        use_current_cache_generation=True,
    )
    db.session.add(ref_cache)
    return ref_cache


@pytest.fixture()
def with_single_process_caller(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    request.getfixturevalue("with_clean_cache")
    ReferenceCacheService.add_new_generation({})
    cache_generation = CacheGenerationModel(cache_table="reference_cache")
    db.session.add(cache_generation)
    db.session.commit()
    called_cache = create_reference_cache("called_once")
    calling_cache = create_reference_cache("calling_cache")
    db.session.add(called_cache)
    db.session.add(calling_cache)
    db.session.commit()
    ProcessCallerService.add_caller(calling_cache.identifier, [called_cache.identifier])
    db.session.commit()
    yield


@pytest.fixture()
def with_multiple_process_callers(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    request.getfixturevalue("with_clean_cache")
    ReferenceCacheService.add_new_generation({})
    called_cache = create_reference_cache("called_many")

    for ref_identifier in ["one_caller", "two_caller", "three_caller"]:
        calling_cache = create_reference_cache(ref_identifier)
        db.session.commit()
        ProcessCallerService.add_caller(calling_cache.identifier, [called_cache.identifier])
    db.session.commit()

    yield


class TestProcessCallerService(BaseTest):
    @pytest.mark.usefixtures("with_no_process_callers")
    def test_has_zero_count_when_empty(self) -> None:
        assert ProcessCallerService.count() == 0

    @pytest.mark.usefixtures("with_multiple_process_callers")
    def test_has_expected_count_when_not_empty(self) -> None:
        assert ProcessCallerService.count() == 3

    @pytest.mark.usefixtures("with_multiple_process_callers")
    def test_can_clear_the_cache(self) -> None:
        ProcessCallerService.clear_cache()
        assert ProcessCallerService.count() == 0

    @pytest.mark.usefixtures("with_no_process_callers")
    def test_can_clear_the_cache_when_empty(self) -> None:
        ProcessCallerService.clear_cache()
        assert ProcessCallerService.count() == 0

    @pytest.mark.usefixtures("with_single_process_caller")
    def test_can_clear_the_cache_for_process_id(self) -> None:
        assert ProcessCallerService.count() != 0
        reference_cache = ReferenceCacheModel.basic_query().filter_by(identifier="called_once").first()
        assert reference_cache is not None
        ProcessCallerService.clear_cache_for_process_ids([reference_cache.id])
        assert ProcessCallerService.count() == 0

    @pytest.mark.usefixtures("with_multiple_process_callers")
    def test_can_clear_the_cache_for_calling_process_id(self) -> None:
        reference_cache = ReferenceCacheModel.basic_query().filter_by(identifier="one_caller").first()
        assert reference_cache is not None
        assert ProcessCallerService.count() == 3
        ProcessCallerService.clear_cache_for_process_ids([reference_cache.id])
        assert ProcessCallerService.count() == 2

    @pytest.mark.usefixtures("with_single_process_caller", "with_multiple_process_callers")
    def test_can_clear_the_cache_for_callee_caller_process_id(
        self,
    ) -> None:
        reference_cache = ReferenceCacheModel.basic_query().filter_by(identifier="one_caller").first()
        assert reference_cache is not None
        assert ProcessCallerService.count() == 4
        ProcessCallerService.clear_cache_for_process_ids([reference_cache.id])
        assert ProcessCallerService.count() == 3

    @pytest.mark.usefixtures("with_single_process_caller", "with_multiple_process_callers")
    def test_can_clear_the_cache_for_process_id_and_leave_other_process_ids_alone(
        self,
    ) -> None:
        reference_cache = ReferenceCacheModel.basic_query().filter_by(identifier="called_many").first()
        assert reference_cache is not None
        ProcessCallerService.clear_cache_for_process_ids([reference_cache.id])
        assert ProcessCallerService.count() == 1

    @pytest.mark.usefixtures("with_no_process_callers")
    def test_raises_if_calling_reference_cache_does_not_exist(self) -> None:
        with pytest.raises(CallingProcessNotFoundError):
            ProcessCallerService.add_caller("DNE", [])
            assert ProcessCallerService.count() == 0

    @pytest.mark.usefixtures("with_single_process_caller")
    def test_raises_if_called_reference_cache_does_not_exist(self) -> None:
        db.session.commit()
        with pytest.raises(CalledProcessNotFoundError):
            ProcessCallerService.add_caller("calling_cache", ["DNE"])
            assert ProcessCallerService.count() == 0
