import unittest

from spiffworkflow_backend.helpers.public_api_urls import build_public_api_v1_url


class TestApiVersion(unittest.TestCase):
    def test_build_public_api_url_appends_api_version_under_root_backend_url(self) -> None:
        url = build_public_api_v1_url("https://backend.example.com", "status")
        self.assertEqual(url, "https://backend.example.com/v1.0/status")

    def test_build_public_api_url_appends_api_version_under_mounted_backend_path(self) -> None:
        url = build_public_api_v1_url("https://backend.example.com/api", "tasks/1/callback")
        self.assertEqual(url, "https://backend.example.com/api/v1.0/tasks/1/callback")

    def test_build_public_api_url_preserves_duplicate_path_segments_when_configured(self) -> None:
        url = build_public_api_v1_url("https://backend.example.com/api/api", "status")
        self.assertEqual(url, "https://backend.example.com/api/api/v1.0/status")
