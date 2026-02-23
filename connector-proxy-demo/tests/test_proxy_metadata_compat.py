from unittest.mock import patch

from app import app


class FakeCommand:
    def __init__(self, url: str):
        self.url = url

    def execute(self, _config: dict, _task_data: dict) -> dict:
        return {
            "response": '{"ok": true}',
            "status": 200,
            "mimetype": "application/json",
        }


class FakeCommandAcceptingMetadata:
    last_callback_url = None

    def __init__(self, url: str, spiff__callback_url: str):
        self.url = url
        self.spiff__callback_url = spiff__callback_url
        FakeCommandAcceptingMetadata.last_callback_url = spiff__callback_url

    def execute(self, _config: dict, _task_data: dict) -> dict:
        return {
            "response": {"ok": True, "callback_url": self.spiff__callback_url},
            "status": 200,
            "mimetype": "application/json",
        }


class FakeCommandWithDefaultInit:
    def execute(self, _config: dict, _task_data: dict) -> dict:
        return {
            "response": {"ok": True},
            "status": 200,
            "mimetype": "application/json",
        }


def test_do_command_drops_constructor_unsupported_kwargs() -> None:
    with app.test_client() as client:
        with patch("spiffworkflow_proxy.blueprint.PluginService.command_named", return_value=FakeCommand):
            response = client.post(
                "/v1/do/http/GetRequestV2",
                json={
                    "url": "https://example.com",
                    "spiff__process_instance_id": 123,
                    "spiff__task_id": "abc",
                    "spiff__callback_url": "https://callback.example.test",
                    "spiff__task_data": {"x": 1},
                    "unknown_param": "drop-me",
                },
            )

    assert response.status_code == 200
    assert response.json == {"ok": True}


def test_do_command_drops_kwargs_for_default_object_init() -> None:
    with app.test_client() as client:
        with patch(
            "spiffworkflow_proxy.blueprint.PluginService.command_named",
            return_value=FakeCommandWithDefaultInit,
        ):
            response = client.post(
                "/v1/do/http/GetRequestV2",
                json={
                    "url": "https://example.com",
                    "spiff__callback_url": "https://callback.example.test",
                    "spiff__process_instance_id": 123,
                    "spiff__task_data": {"x": 1},
                },
            )

    assert response.status_code == 200
    assert response.json == {"ok": True}


def test_do_command_preserves_supported_spiff_metadata_kwargs() -> None:
    with app.test_client() as client:
        with patch(
            "spiffworkflow_proxy.blueprint.PluginService.command_named",
            return_value=FakeCommandAcceptingMetadata,
        ):
            response = client.post(
                "/v1/do/http/GetRequestV2",
                json={
                    "url": "https://example.com",
                    "spiff__callback_url": "https://callback.example.test",
                    "spiff__process_instance_id": 123,
                    "spiff__task_data": {"x": 1},
                },
            )

    assert response.status_code == 200
    assert response.json == {"ok": True, "callback_url": "https://callback.example.test"}
    assert FakeCommandAcceptingMetadata.last_callback_url == "https://callback.example.test"
