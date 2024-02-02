from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

import pytest
from flask.app import Flask
from spiffworkflow_backend.data_stores.kkv import KKVDataStore
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.kkv_data_store import KKVDataStoreModel

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


@dataclass
class MockTask:
    data: dict[str, Any]


@pytest.fixture()
def with_clean_data_store(app: Flask, with_db_and_bpmn_file_cleanup: None) -> Generator[None, None, None]:
    db.session.query(KKVDataStoreModel).delete()
    db.session.commit()
    yield


@pytest.fixture()
def with_key1_key2_record(with_clean_data_store: None) -> Generator[None, None, None]:
    model = KKVDataStoreModel(top_level_key="key1", secondary_key="key2", value="value1")
    db.session.add(model)
    db.session.commit()
    yield


class TestKKVDataStore(BaseTest):
    """Infer from class name."""

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
        assert result == "value1"

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

    def test_can_insert_a_value(self, with_clean_data_store: None) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={"the_id": {"newKey1": {"newKey2": "newValue"}}})
        kkv_data_store.set(my_task)
        count = db.session.query(KKVDataStoreModel).count()
        assert count == 1

    def test_can_insert_mulitple_values_for_same_top_key(self, with_clean_data_store: None) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={"the_id": {"newKey1": {"newKey2": "newValue", "newKey3": "newValue2"}}})
        kkv_data_store.set(my_task)
        count = db.session.query(KKVDataStoreModel).count()
        assert count == 2

    def test_can_insert_mulitple_values_for_different_top_key(self, with_clean_data_store: None) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={"the_id": {"newKey1": {"newKey2": "newValue"}, "newKey3": {"newKey4": "newValue2"}}})
        kkv_data_store.set(my_task)
        count = db.session.query(KKVDataStoreModel).count()
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

    def test_can_update_a_value(self, with_clean_data_store: None) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={"the_id": {"newKey1": {"newKey2": "newValue"}}})
        kkv_data_store.set(my_task)
        my_task.data = {"the_id": {"newKey1": {"newKey2": "newValue2"}}}
        kkv_data_store.set(my_task)
        count = db.session.query(KKVDataStoreModel).count()
        assert count == 1
        kkv_data_store.get(my_task)
        result2 = my_task.data["the_id"]("newKey1", "newKey2")
        assert result2 == "newValue2"

    def test_can_delete_record_by_nulling_a_secondary_key(self, with_key1_key2_record: None) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={"the_id": {"key1": {"key2": None}}})
        kkv_data_store.set(my_task)
        kkv_data_store.get(my_task)
        result = my_task.data["the_id"]("key1", "key2")
        assert result is None
        count = db.session.query(KKVDataStoreModel).count()
        assert count == 0

    def test_can_delete_all_records_by_nulling_a_top_level_key(self, with_clean_data_store: None) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={"the_id": {"newKey1": {"newKey2": "newValue", "newKey3": "newValue2"}}})
        kkv_data_store.set(my_task)
        my_task.data = {"the_id": {"newKey1": None}}
        kkv_data_store.set(my_task)
        count = db.session.query(KKVDataStoreModel).count()
        assert count == 0

    def test_top_key_delete_does_not_delete_for_other_top_levels(self, with_clean_data_store: None) -> None:
        kkv_data_store = KKVDataStore("the_id", "the_name")
        my_task = MockTask(data={"the_id": {"newKey1": {"newKey2": "newValue"}, "newKey3": {"newKey4": "newValue2"}}})
        kkv_data_store.set(my_task)
        my_task.data = {"the_id": {"newKey1": None}}
        kkv_data_store.set(my_task)
        count = db.session.query(KKVDataStoreModel).count()
        assert count == 1
        kkv_data_store.get(my_task)
        result = my_task.data["the_id"]("newKey3", "newKey4")
        assert result == "newValue2"
