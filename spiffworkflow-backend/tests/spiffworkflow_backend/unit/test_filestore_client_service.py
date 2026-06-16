from unittest.mock import MagicMock

import pytest
import requests
from flask import Flask

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.services.filestore_client_service import FilestoreClientService


class TestFilestoreClientService:
    @pytest.fixture(autouse=True)
    def filestore_config(self, app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setitem(app.config, "SPIFFWORKFLOW_BACKEND_FILESTORE_URL", "https://files.example.com")
        monkeypatch.setitem(app.config, "SPIFFWORKFLOW_BACKEND_FILESTORE_SHARED_SECRET", "secret")
        monkeypatch.setitem(app.config, "SPIFFWORKFLOW_BACKEND_FILESTORE_TENANT_ID", "tenant")

    def test_post_wraps_request_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "spiffworkflow_backend.services.filestore_client_service.requests.post",
            MagicMock(side_effect=requests.Timeout("timed out")),
        )

        with pytest.raises(ApiError) as exception_info:
            FilestoreClientService._post("/v1/projects", {}, "Could not sync")

        assert exception_info.value.error_code == "filestore_sync_failed"
        assert exception_info.value.status_code == 502
        assert "request failed: timed out" in exception_info.value.message

    def test_post_wraps_invalid_json_response(self, monkeypatch: pytest.MonkeyPatch) -> None:
        response = MagicMock(status_code=200)
        response.json.side_effect = ValueError("not json")
        monkeypatch.setattr(
            "spiffworkflow_backend.services.filestore_client_service.requests.post",
            MagicMock(return_value=response),
        )

        with pytest.raises(ApiError) as exception_info:
            FilestoreClientService._post("/v1/projects", {}, "Could not sync")

        assert exception_info.value.error_code == "filestore_sync_failed"
        assert exception_info.value.status_code == 502
        assert "invalid JSON response: not json" in exception_info.value.message

    def test_tenant_id_raises_api_error_when_tenant_configs_are_missing(
        self, app: Flask, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delitem(app.config, "SPIFFWORKFLOW_BACKEND_FILESTORE_TENANT_ID")
        monkeypatch.delitem(app.config, "ENV_IDENTIFIER")

        with pytest.raises(ApiError) as exception_info:
            FilestoreClientService.tenant_id()

        assert exception_info.value.error_code == "filestore_tenant_id_not_configured"
        assert exception_info.value.status_code == 501

    @pytest.mark.parametrize("tenant_id", ["", "   "])
    def test_tenant_id_raises_api_error_when_tenant_id_is_empty(
        self, app: Flask, monkeypatch: pytest.MonkeyPatch, tenant_id: str
    ) -> None:
        monkeypatch.setitem(app.config, "SPIFFWORKFLOW_BACKEND_FILESTORE_TENANT_ID", tenant_id)

        with pytest.raises(ApiError) as exception_info:
            FilestoreClientService.tenant_id()

        assert exception_info.value.error_code == "filestore_tenant_id_not_configured"
        assert exception_info.value.status_code == 501
        assert "must be a non-empty string" in exception_info.value.message
