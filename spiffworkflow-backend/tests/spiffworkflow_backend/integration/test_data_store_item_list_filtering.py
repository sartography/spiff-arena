from collections.abc import Generator

import pytest
from flask import Flask
from httpx import Response
from starlette.testclient import TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.kkv_data_store import KKVDataStoreModel
from spiffworkflow_backend.models.kkv_data_store_entry import KKVDataStoreEntryModel
from spiffworkflow_backend.models.user import UserModel
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


@pytest.fixture()
def with_populated_kkv_store(app: Flask, with_db_and_bpmn_file_cleanup: None) -> Generator[KKVDataStoreModel, None, None]:
    db.session.query(KKVDataStoreEntryModel).delete()
    db.session.query(KKVDataStoreModel).delete()
    db.session.commit()

    model = KKVDataStoreModel(identifier="test_store", name="Test Store", location="test_location", schema={})
    db.session.add(model)
    db.session.commit()

    entries = [
        KKVDataStoreEntryModel(
            kkv_data_store_id=model.id,
            top_level_key="instance_1",
            secondary_key="model_a",
            value={"status": "complete"},
        ),
        KKVDataStoreEntryModel(
            kkv_data_store_id=model.id,
            top_level_key="instance_1",
            secondary_key="model_b",
            value={"status": "pending"},
        ),
        KKVDataStoreEntryModel(
            kkv_data_store_id=model.id,
            top_level_key="instance_2",
            secondary_key="model_a",
            value={"status": "active"},
        ),
        KKVDataStoreEntryModel(
            kkv_data_store_id=model.id,
            top_level_key="instance_2",
            secondary_key="model_c",
            value={"status": "error"},
        ),
        KKVDataStoreEntryModel(
            kkv_data_store_id=model.id,
            top_level_key="instance_3",
            secondary_key="model_b",
            value={"status": "complete"},
        ),
    ]
    db.session.add_all(entries)
    db.session.commit()

    yield model


class TestDataStoreItemListFiltering(BaseTest):
    """Tests for GET /data-stores/kkv/{identifier}/items with top_level_key and/or secondary_key filters."""

    def _get(
        self,
        client: TestClient,
        user: UserModel,
        identifier: str = "test_store",
        location: str = "test_location",
        top_level_key: str | None = None,
        secondary_key: str | None = None,
    ) -> Response:
        url = f"/v1.0/data-stores/kkv/{identifier}/items?location={location}"
        if top_level_key is not None:
            url += f"&top_level_key={top_level_key}"
        if secondary_key is not None:
            url += f"&secondary_key={secondary_key}"
        return client.get(url, headers=self.logged_in_headers(user))

    @pytest.mark.usefixtures("with_populated_kkv_store")
    def test_filter_by_top_level_key_only(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        response = self._get(client, with_super_admin_user, top_level_key="instance_1")
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 2
        assert all(r["top_level_key"] == "instance_1" for r in results)

    @pytest.mark.usefixtures("with_populated_kkv_store")
    def test_filter_by_secondary_key_only(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        response = self._get(client, with_super_admin_user, secondary_key="model_a")
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 2
        assert all(r["secondary_key"] == "model_a" for r in results)

    @pytest.mark.usefixtures("with_populated_kkv_store")
    def test_filter_by_both_keys(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        response = self._get(
            client,
            with_super_admin_user,
            top_level_key="instance_1",
            secondary_key="model_b",
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["top_level_key"] == "instance_1"
        assert results[0]["secondary_key"] == "model_b"
        assert results[0]["value"] == {"status": "pending"}

    @pytest.mark.usefixtures("with_populated_kkv_store")
    def test_filter_returns_empty_for_no_match(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        response = self._get(client, with_super_admin_user, top_level_key="nonexistent")
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 0
        assert response.json()["pagination"]["total"] == 0

    @pytest.mark.usefixtures("with_populated_kkv_store")
    def test_no_filter_returns_all_items_via_standard_path(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """When neither key is provided, should return all entries in flat format."""
        response = self._get(client, with_super_admin_user)
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 5
        assert all("top_level_key" in r and "secondary_key" in r and "value" in r for r in results)

    @pytest.mark.usefixtures("with_populated_kkv_store")
    def test_filter_returns_404_for_nonexistent_store(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        response = self._get(client, with_super_admin_user, identifier="no_such_store", top_level_key="x")
        assert response.status_code == 404

    @pytest.mark.usefixtures("with_populated_kkv_store")
    def test_filter_pagination(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        url = "/v1.0/data-stores/kkv/test_store/items?location=test_location&secondary_key=model_b&per_page=1&page=1"
        response = client.get(url, headers=self.logged_in_headers(with_super_admin_user))
        assert response.status_code == 200
        assert len(response.json()["results"]) == 1
        assert response.json()["pagination"]["total"] == 2
        assert response.json()["pagination"]["pages"] == 2

    @pytest.mark.usefixtures("with_populated_kkv_store")
    def test_paginate_false_returns_all_results(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        url = "/v1.0/data-stores/kkv/test_store/items?location=test_location&paginate=false"
        response = client.get(url, headers=self.logged_in_headers(with_super_admin_user))
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 5
        assert response.json()["pagination"]["total"] == 5
        assert response.json()["pagination"]["pages"] == 1

    @pytest.mark.usefixtures("with_populated_kkv_store")
    def test_paginate_false_with_filter(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        url = "/v1.0/data-stores/kkv/test_store/items?location=test_location&secondary_key=model_a&paginate=false"
        response = client.get(url, headers=self.logged_in_headers(with_super_admin_user))
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 2
        assert all(r["secondary_key"] == "model_a" for r in results)
        assert response.json()["pagination"]["total"] == 2
        assert response.json()["pagination"]["pages"] == 1
