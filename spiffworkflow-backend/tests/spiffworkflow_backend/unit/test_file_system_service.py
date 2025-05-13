from spiffworkflow_backend.services.file_system_service import FileSystemService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestFileSystemService(BaseTest):
    def test_path_join(self) -> None:
        test_cases = {
            "/root/path/hey": ["/root/path", "/hey"],
            "/root/path/hey1": ["/root/path", "hey1"],
            "/root/path/hey/bob": ["/root/path", "hey", "/bob"],
        }
        for expected_path, input in test_cases.items():
            assert FileSystemService.path_join(*input) == expected_path
