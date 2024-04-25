from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

import pytest
from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.data_stores.kkv import KKVDataStore
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.kkv_data_store import KKVDataStoreModel
from spiffworkflow_backend.models.kkv_data_store_entry import KKVDataStoreEntryModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


@dataclass
class MockTask:
    data: dict[str, Any]


@pytest.fixture()
def with_clean_data_store(app: Flask, with_db_and_bpmn_file_cleanup: None) -> Generator[KKVDataStoreModel, None, None]:
    app.config["THREAD_LOCAL_DATA"].process_model_identifier = "the_location/of/some/process-model"

    db.session.query(KKVDataStoreModel).delete()
    db.session.commit()

    model = KKVDataStoreModel(identifier="the_id", name="the_name", location="the_location", schema={})
    db.session.add(model)
    db.session.commit()

    yield model


@pytest.fixture()
def with_key1_key2_record(with_clean_data_store: KKVDataStoreModel) -> Generator[KKVDataStoreModel, None, None]:
    model = KKVDataStoreEntryModel(
        kkv_data_store_id=with_clean_data_store.id, top_level_key="key1", secondary_key="key2", value={"key": "value"}
    )
    db.session.add(model)
    db.session.commit()

    yield with_clean_data_store


class TestKkvDataStore(BaseTest):
    """Infer from class name."""

    def _entry_count(self, model: KKVDataStoreModel) -> int:
        return db.session.query(KKVDataStoreEntryModel).filter_by(kkv_data_store_id=model.id).count()

    def test_returns_none_if_no_records_exist(self, with_clean_data_store: None) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={})
        kkv_data_store.get(my_task)
        assert len(my_task.data) == 1
        result = my_task.data["the_id"]("key1", "key2")
        assert result is None

    def test_can_return_value_if_both_keys_match(self, with_key1_key2_record: None) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={})
        kkv_data_store.get(my_task)
        assert len(my_task.data) == 1
        result = my_task.data["the_id"]("key1", "key2")
        assert result == {"key": "value"}

    def test_returns_none_if_first_key_does_not_match(self, with_key1_key2_record: None) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={})
        kkv_data_store.get(my_task)
        assert len(my_task.data) == 1
        result = my_task.data["the_id"]("key11", "key2")
        assert result is None

    def test_returns_none_if_second_key_does_not_match(self, with_key1_key2_record: None) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={})
        kkv_data_store.get(my_task)
        assert len(my_task.data) == 1
        result = my_task.data["the_id"]("key1", "key22")
        assert result is None

    def test_can_insert_a_value(self, with_clean_data_store: KKVDataStoreModel) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={"the_id": {"newKey1": {"newKey2": "newValue"}}})
        kkv_data_store.set(my_task)
        count = self._entry_count(with_clean_data_store)
        assert count == 1

    def test_can_insert_multiple_values_for_same_top_key(self, with_clean_data_store: KKVDataStoreModel) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={"the_id": {"newKey1": {"newKey2": "newValue", "newKey3": "newValue2"}}})
        kkv_data_store.set(my_task)
        count = self._entry_count(with_clean_data_store)
        assert count == 2

    def test_can_insert_multiple_values_for_different_top_key(self, with_clean_data_store: KKVDataStoreModel) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={"the_id": {"newKey1": {"newKey2": "newValue"}, "newKey3": {"newKey4": "newValue2"}}})
        kkv_data_store.set(my_task)
        count = self._entry_count(with_clean_data_store)
        assert count == 2

    def test_value_is_removed_from_task_data_after_insert(self, with_clean_data_store: None) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={"the_id": {"newKey1": {"newKey2": "newValue"}, "newKey3": {"newKey4": "newValue2"}}})
        kkv_data_store.set(my_task)
        assert "the_id" not in my_task.data

    def test_can_get_after_a_set(self, with_clean_data_store: None) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={"the_id": {"newKey1": {"newKey2": "newValue"}, "newKey3": {"newKey4": "newValue2"}}})
        kkv_data_store.set(my_task)
        kkv_data_store.get(my_task)
        result1 = my_task.data["the_id"]("newKey1", "newKey2")
        assert result1 == "newValue"
        result2 = my_task.data["the_id"]("newKey3", "newKey4")
        assert result2 == "newValue2"

    def test_can_update_a_value(self, with_clean_data_store: KKVDataStore) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={"the_id": {"newKey1": {"newKey2": "newValue"}}})
        kkv_data_store.set(my_task)
        my_task.data = {"the_id": {"newKey1": {"newKey2": "newValue2"}}}
        kkv_data_store.set(my_task)
        count = self._entry_count(with_clean_data_store)
        assert count == 1
        kkv_data_store.get(my_task)
        result2 = my_task.data["the_id"]("newKey1", "newKey2")
        assert result2 == "newValue2"

    def test_can_delete_record_by_nulling_a_secondary_key(self, with_key1_key2_record: KKVDataStoreModel) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={"the_id": {"key1": {"key2": None}}})
        kkv_data_store.set(my_task)
        kkv_data_store.get(my_task)
        result = my_task.data["the_id"]("key1", "key2")
        assert result is None
        count = self._entry_count(with_key1_key2_record)
        assert count == 0

    def test_can_delete_all_records_by_nulling_a_top_level_key(self, with_clean_data_store: KKVDataStoreModel) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={"the_id": {"newKey1": {"newKey2": "newValue", "newKey3": "newValue2"}}})
        kkv_data_store.set(my_task)
        my_task.data = {"the_id": {"newKey1": None}}
        kkv_data_store.set(my_task)
        count = self._entry_count(with_clean_data_store)
        assert count == 0

    def test_top_key_delete_does_not_delete_for_other_top_levels(self, with_clean_data_store: KKVDataStoreModel) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={"the_id": {"newKey1": {"newKey2": "newValue"}, "newKey3": {"newKey4": "newValue2"}}})
        kkv_data_store.set(my_task)
        my_task.data = {"the_id": {"newKey1": None}}
        kkv_data_store.set(my_task)
        count = self._entry_count(with_clean_data_store)
        assert count == 1
        kkv_data_store.get(my_task)
        result = my_task.data["the_id"]("newKey3", "newKey4")
        assert result == "newValue2"

    def test_can_retrieve_data_store_from_script_task(
        self, app: Flask, client: FlaskClient, with_db_and_bpmn_file_cleanup: None, with_clean_data_store: KKVDataStoreModel
    ) -> None:
        process_model_identifier = "simple_data_store"
        bpmn_file_location = "data_store_simple"
        bpmn_file_name = "data-store-simple.bpmn"
        process_model = load_test_spec(
            process_model_id=process_model_identifier,
            bpmn_file_name=bpmn_file_name,
            process_model_source_directory=bpmn_file_location,
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
        assert process_instance.status == "complete"

    def test_can_retrieve_data_store_from_script_task_with_instructions(
        self, app: Flask, client: FlaskClient, with_db_and_bpmn_file_cleanup: None, with_clean_data_store: KKVDataStoreModel
    ) -> None:
        process_model_identifier = "simple_data_store"
        bpmn_file_location = "data_store_simple"
        bpmn_file_name = "data-store-simple.bpmn"
        process_model = load_test_spec(
            process_model_id=process_model_identifier,
            bpmn_file_name=bpmn_file_name,
            process_model_source_directory=bpmn_file_location,
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="run_until_user_message")
        assert process_instance.status == "running"

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        assert process_instance is not None
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
        assert process_instance.status == "complete"
