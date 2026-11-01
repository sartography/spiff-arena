from spiffworkflow_backend.helpers.public_api_urls import build_public_api_v1_url


def test_build_public_api_url_appends_api_version_under_root_backend_url() -> None:
    url = build_public_api_v1_url("https://backend.example.com", "status")
    assert url == "https://backend.example.com/v1.0/status"


def test_build_public_api_url_appends_api_version_under_mounted_backend_path() -> None:
    url = build_public_api_v1_url("https://backend.example.com/api", "tasks/1/callback")
    assert url == "https://backend.example.com/api/v1.0/tasks/1/callback"


def test_build_public_api_url_preserves_duplicate_path_segments_when_configured() -> None:
    url = build_public_api_v1_url("https://backend.example.com/api/api", "status")
    assert url == "https://backend.example.com/api/api/v1.0/status"
