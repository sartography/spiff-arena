import os

from spiffworkflow_backend.models.file import FileModel
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.file_system_service import FileSystemService


class BootstrapProvider:
    """Provide all the data needed for the test_bootstrap test."""

    def get_user(self) -> UserModel:
        return UserModel(
            username="bootstrap_user",
            email="bootstrap_user@example.com",
            first_name="Bootstrap",
            last_name="User",
        )

    def get_groups(self) -> list[GroupModel]:
        return [
            GroupModel(
                identifier="bootstrap_group",
                display_name="Bootstrap Group",
            )
        ]

    def get_files(self) -> list[FileModel]:
        readme_path = os.path.join(
            FileSystemService.root_path(), "sample-process-models", "a_process", "README.md"
        )
        return [
            FileModel(
                name="README.md",
                content=open(readme_path).read(),
                process_model_id="a_process",
            )
        ]
