from collections.abc import Generator

import pytest
from flask import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.kkv_data_store import KKVDataStoreModel
from spiffworkflow_backend.models.kkv_data_store_entry import KKVDataStoreEntryModel
from spiffworkflow_backend.models.user import UserModel
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


@pytest.fixture()
def with_clean_kkv_store(app: Flask, with_db_and_bpmn_file_cleanup: None) -> Generator[KKVDataStoreModel, None, None]:
    db.session.query(KKVDataStoreModel).delete()
    db.session.commit()

    model = KKVDataStoreModel(identifier="test_store", name="Test Store", location="test_location", schema={})
    db.session.add(model)
    db.session.commit()

    yield model


def _entry_count(store: KKVDataStoreModel) -> int:
    return db.session.query(KKVDataStoreEntryModel).filter_by(kkv_data_store_id=store.id).count()


def _get_entry(store: KKVDataStoreModel, top_key: str, sec_key: str) -> KKVDataStoreEntryModel | None:
    return (
        db.session.query(KKVDataStoreEntryModel)
        .filter_by(kkv_data_store_id=store.id, top_level_key=top_key, secondary_key=sec_key)
        .first()
    )


class TestDataStoreWriteItems(BaseTest):
    """Tests for PUT /data-stores/{data_store_type}/{identifier}/items."""

    def _put(
        self,
        client: TestClient,
        user: UserModel,
        identifier: str,
        body: dict,
        location: str | None = "test_location",
    ) -> TestClient:
        url = f"/v1.0/data-stores/kkv/{identifier}/items"
        if location is not None:
            url += f"?location={location}"
        return client.put(
            url,
            headers=self.logged_in_headers(user),
            json=body,
        )

    # --- Insert tests ---

    def test_can_insert_a_single_entry(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        response = self._put(
            client,
            with_super_admin_user,
            "test_store",
            {"top1": {"sec1": {"field": "value"}}},
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True
        assert _entry_count(with_clean_kkv_store) == 1
        entry = _get_entry(with_clean_kkv_store, "top1", "sec1")
        assert entry is not None
        assert entry.value == {"field": "value"}

    def test_can_insert_multiple_secondary_keys(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        response = self._put(
            client,
            with_super_admin_user,
            "test_store",
            {"top1": {"sec1": "val1", "sec2": "val2"}},
        )
        assert response.status_code == 200
        assert _entry_count(with_clean_kkv_store) == 2

    def test_can_insert_multiple_top_level_keys(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        response = self._put(
            client,
            with_super_admin_user,
            "test_store",
            {
                "top1": {"sec1": "val1"},
                "top2": {"sec2": "val2"},
            },
        )
        assert response.status_code == 200
        assert _entry_count(with_clean_kkv_store) == 2

    # --- Update tests ---

    def test_can_update_an_existing_entry(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        self._put(client, with_super_admin_user, "test_store", {"top1": {"sec1": "original"}})
        response = self._put(client, with_super_admin_user, "test_store", {"top1": {"sec1": "updated"}})
        assert response.status_code == 200
        assert _entry_count(with_clean_kkv_store) == 1
        entry = _get_entry(with_clean_kkv_store, "top1", "sec1")
        assert entry is not None
        assert entry.value == "updated"

    # --- Delete tests ---

    def test_can_delete_entry_by_nulling_secondary_key(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        self._put(
            client,
            with_super_admin_user,
            "test_store",
            {"top1": {"sec1": "val1", "sec2": "val2"}},
        )
        assert _entry_count(with_clean_kkv_store) == 2

        response = self._put(client, with_super_admin_user, "test_store", {"top1": {"sec1": None}})
        assert response.status_code == 200
        assert _entry_count(with_clean_kkv_store) == 1
        assert _get_entry(with_clean_kkv_store, "top1", "sec1") is None
        assert _get_entry(with_clean_kkv_store, "top1", "sec2") is not None

    def test_can_delete_all_entries_by_nulling_top_level_key(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        self._put(
            client,
            with_super_admin_user,
            "test_store",
            {"top1": {"sec1": "val1", "sec2": "val2"}},
        )
        assert _entry_count(with_clean_kkv_store) == 2

        response = self._put(client, with_super_admin_user, "test_store", {"top1": None})
        assert response.status_code == 200
        assert _entry_count(with_clean_kkv_store) == 0

    def test_null_secondary_key_for_nonexistent_entry_is_noop(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        response = self._put(client, with_super_admin_user, "test_store", {"top1": {"sec1": None}})
        assert response.status_code == 200
        assert _entry_count(with_clean_kkv_store) == 0

    # --- Error handling ---

    def test_returns_404_for_nonexistent_store(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        response = self._put(
            client,
            with_super_admin_user,
            "nonexistent_store",
            {"top1": {"sec1": "val1"}},
        )
        assert response.status_code == 404

    def test_returns_400_for_non_kkv_type(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        response = client.put(
            "/v1.0/data-stores/json/test_store/items?location=test_location",
            headers=self.logged_in_headers(with_super_admin_user),
            json={"top1": {"sec1": "val1"}},
        )
        assert response.status_code == 400

    def test_returns_400_for_invalid_body(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        headers = self.logged_in_headers(with_super_admin_user)
        headers["Content-Type"] = "application/json"
        response = client.put(
            "/v1.0/data-stores/kkv/test_store/items?location=test_location",
            headers=headers,
            content=b"not json",
        )
        assert response.status_code == 400

    def test_returns_400_for_non_dict_secondary_level(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        response = self._put(client, with_super_admin_user, "test_store", {"top1": "not_a_dict"})
        assert response.status_code == 400

    # --- Complex value types ---

    def test_can_store_list_values(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        data = [{"name": "exclusionsText", "value": "CE text"}]
        response = self._put(
            client,
            with_super_admin_user,
            "test_store",
            {"pid_42": {"BLM-MOAB-CE": data}},
        )
        assert response.status_code == 200
        entry = _get_entry(with_clean_kkv_store, "pid_42", "BLM-MOAB-CE")
        assert entry is not None
        assert entry.value == data

    def test_can_store_nested_object_values(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        data = {
            "projectLead": {"value": "Analyst Arthur", "comment": {"saved": False}},
            "applicant": {"value": "Various", "comment": {"saved": False}},
        }
        response = self._put(
            client,
            with_super_admin_user,
            "test_store",
            {"pid_42": {"BLM-MOAB-CE": data}},
        )
        assert response.status_code == 200
        entry = _get_entry(with_clean_kkv_store, "pid_42", "BLM-MOAB-CE")
        assert entry is not None
        assert entry.value == data

    # --- Top-level key scoping ---

    def test_delete_does_not_affect_other_top_level_keys(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        self._put(
            client,
            with_super_admin_user,
            "test_store",
            {
                "top1": {"sec1": "val1"},
                "top2": {"sec2": "val2"},
            },
        )
        assert _entry_count(with_clean_kkv_store) == 2

        self._put(client, with_super_admin_user, "test_store", {"top1": None})
        assert _entry_count(with_clean_kkv_store) == 1
        assert _get_entry(with_clean_kkv_store, "top2", "sec2") is not None


class TestDataStoreFilteredGet(BaseTest):
    """Tests for GET /data-stores/kkv/{identifier}/items with top_level_key/secondary_key filters."""

    def _put(
        self,
        client: TestClient,
        user: UserModel,
        identifier: str,
        body: dict,
        location: str = "test_location",
    ) -> TestClient:
        return client.put(
            f"/v1.0/data-stores/kkv/{identifier}/items?location={location}",
            headers=self.logged_in_headers(user),
            json=body,
        )

    def _get(
        self,
        client: TestClient,
        user: UserModel,
        identifier: str,
        location: str = "test_location",
        top_level_key: str | None = None,
        secondary_key: str | None = None,
    ) -> TestClient:
        url = f"/v1.0/data-stores/kkv/{identifier}/items?location={location}"
        if top_level_key is not None:
            url += f"&top_level_key={top_level_key}"
        if secondary_key is not None:
            url += f"&secondary_key={secondary_key}"
        return client.get(url, headers=self.logged_in_headers(user))

    def _seed_data(self, client: TestClient, user: UserModel) -> None:
        self._put(
            client,
            user,
            "test_store",
            {
                "pid_1": {
                    "model_A": [{"name": "field1", "value": "a"}],
                    "model_B": "data_b",
                },
                "pid_2": {"model_A": [{"name": "field2", "value": "c"}]},
            },
        )

    def test_filter_by_top_level_key(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        self._seed_data(client, with_super_admin_user)
        response = self._get(client, with_super_admin_user, "test_store", top_level_key="pid_1")
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 2
        assert all(r["top_level_key"] == "pid_1" for r in results)

    def test_filter_by_top_level_and_secondary_key(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        self._seed_data(client, with_super_admin_user)
        response = self._get(
            client,
            with_super_admin_user,
            "test_store",
            top_level_key="pid_1",
            secondary_key="model_A",
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["top_level_key"] == "pid_1"
        assert results[0]["secondary_key"] == "model_A"
        assert results[0]["value"] == [{"name": "field1", "value": "a"}]

    def test_filter_returns_empty_for_nonexistent_key(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        self._seed_data(client, with_super_admin_user)
        response = self._get(client, with_super_admin_user, "test_store", top_level_key="nonexistent")
        assert response.status_code == 200
        assert response.json()["results"] == []
        assert response.json()["pagination"]["total"] == 0

    def test_filter_returns_404_for_nonexistent_store(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        response = self._get(client, with_super_admin_user, "no_such_store", top_level_key="pid_1")
        assert response.status_code == 404

    def test_unfiltered_get_still_works(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        with_clean_kkv_store: KKVDataStoreModel,
    ) -> None:
        self._seed_data(client, with_super_admin_user)
        response = self._get(client, with_super_admin_user, "test_store")
        assert response.status_code == 200
        assert len(response.json()["results"]) == 3
