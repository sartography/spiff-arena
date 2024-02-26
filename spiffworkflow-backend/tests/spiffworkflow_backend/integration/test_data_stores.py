from flask import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.typeahead import TypeaheadModel
from spiffworkflow_backend.models.user import UserModel

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestDataStores(BaseTest):
    def load_data_store(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """
        Populate a datastore with some mock data using a BPMN process that will load information
        using the typeahead data store.  This should add 77 entries to the typeahead table.
        """
        process_group_id = "data_stores"
        process_model_id = "cereals_data_store"
        bpmn_file_location = "data_stores"
        process_model = self.create_group_and_model_with_bpmn(
            client,
            with_super_admin_user,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
            bpmn_file_location=bpmn_file_location,
        )

        headers = self.logged_in_headers(with_super_admin_user)
        response = self.create_process_instance_from_process_model_id_with_api(client, process_model.id, headers)
        assert response.json is not None
        process_instance_id = response.json["id"]

        client.post(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
            headers=self.logged_in_headers(with_super_admin_user),
        )

    def test_create_data_store_populates_db(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Assure that when we run this workflow it will autofill the typeahead data store."""
        self.load_data_store(app, client, with_db_and_bpmn_file_cleanup, with_super_admin_user)
        typeaheads = TypeaheadModel.query.all()
        assert len(typeaheads) == 153

    def test_get_list_of_data_stores(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """
        It should be possible to get a list of the data store categories that are available.
        """
        results = client.get("/v1.0/data-stores", headers=self.logged_in_headers(with_super_admin_user))
        assert results.json == []

        self.load_data_store(app, client, with_db_and_bpmn_file_cleanup, with_super_admin_user)
        results = client.get("/v1.0/data-stores", headers=self.logged_in_headers(with_super_admin_user))
        assert results.json == [
            {"name": "albums", "type": "typeahead", "id": "albums", "clz": "TypeaheadDataStore"},
            {"name": "cereals", "type": "typeahead", "id": "cereals", "clz": "TypeaheadDataStore"},
        ]

    def test_get_data_store_returns_paginated_results(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.load_data_store(app, client, with_db_and_bpmn_file_cleanup, with_super_admin_user)
        response = client.get(
            "/v1.0/data-stores/typeahead/albums/items?per_page=10", headers=self.logged_in_headers(with_super_admin_user)
        )

        expected_item_in_response = {
            "search_term": "A Vulgar Display Of Power",
            "year": 1992,
            "album": "A Vulgar Display Of Power",
            "artist": "Pantera",
        }

        assert response.json is not None
        assert len(response.json["results"]) == 10
        assert response.json["pagination"]["count"] == 10
        assert response.json["pagination"]["total"] == 76
        assert response.json["pagination"]["pages"] == 8

        assert expected_item_in_response in response.json["results"]
