import json
import os
from collections.abc import Callable
from collections.abc import Generator
from datetime import datetime
from datetime import timezone
from typing import Any

from flask import current_app

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.file import CONTENT_TYPES
from spiffworkflow_backend.models.file import File
from spiffworkflow_backend.models.file import FileType
from spiffworkflow_backend.models.process_model import ProcessModelInfo


class ProcessModelFileNotFoundError(Exception):
    pass


DirectoryPredicate = Callable[[str, int], bool] | None
FilePredicate = Callable[[str], bool] | None
FileGenerator = Generator[str, None, None]


class FileSystemService:
    """Simple Service meant for extension that provides some useful
    methods for dealing with the File system.
    """

    PROCESS_GROUP_JSON_FILE = "process_group.json"
    PROCESS_MODEL_JSON_FILE = "process_model.json"

    @classmethod
    def walk_files(cls, start_dir: str, directory_predicate: DirectoryPredicate, file_predicate: FilePredicate) -> FileGenerator:
        depth = 0
        for root, subdirs, files in os.walk(start_dir):
            if directory_predicate:
                subdirs[:] = [dir for dir in subdirs if directory_predicate(dir, depth)]
            for f in files:
                file = os.path.join(root, f)
                if file_predicate and not file_predicate(file):
                    continue
                yield file
            depth += 1

    @classmethod
    def non_git_dir(cls, dirname: str, depth: int) -> bool:
        return dirname != ".git"

    @classmethod
    def not_recursive(cls, dirname: str, depth: int) -> bool:
        return depth == 0

    @classmethod
    def standard_directory_predicate(cls, recursive: bool) -> DirectoryPredicate:
        return cls.non_git_dir if recursive else cls.not_recursive

    @classmethod
    def is_process_model_json_file(cls, file: str) -> bool:
        return file.endswith(cls.PROCESS_MODEL_JSON_FILE)

    @classmethod
    def is_process_group_json_file(cls, file: str) -> bool:
        return file.endswith(cls.PROCESS_GROUP_JSON_FILE)

    @classmethod
    def is_data_store_json_file(cls, file: str) -> bool:
        return file.endswith("_datastore.json")

    @classmethod
    def walk_files_from_root_path(cls, recursive: bool, file_predicate: FilePredicate) -> FileGenerator:
        yield from cls.walk_files(cls.root_path(), cls.standard_directory_predicate(recursive), file_predicate)

    @staticmethod
    def root_path() -> str:
        dir_name = current_app.config["SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR"]
        # ensure this is a string - thanks mypy...
        return os.path.abspath(os.path.join(dir_name, ""))

    @staticmethod
    def id_string_to_relative_path(id_string: str) -> str:
        return id_string.replace("/", os.sep)

    @classmethod
    def full_path_from_id(cls, id: str) -> str:
        return os.path.abspath(
            os.path.join(
                cls.root_path(),
                cls.id_string_to_relative_path(id),
            )
        )

    @classmethod
    def get_files(
        cls,
        process_model_info: ProcessModelInfo,
        file_name: str | None = None,
        extension_filter: str = "",
    ) -> list[File]:
        """Return all files associated with a workflow specification."""
        path = os.path.join(FileSystemService.root_path(), process_model_info.id_for_file_path())
        files = cls._get_files(path, file_name)
        if extension_filter != "":
            files = list(filter(lambda file: file.name.endswith(extension_filter), files))
        return files

    @classmethod
    def get_sorted_files(
        cls,
        process_model_info: ProcessModelInfo,
    ) -> list[File]:
        files = sorted(
            FileSystemService.get_files(process_model_info),
            key=lambda f: "" if f.name == process_model_info.primary_file_name else f.sort_index,
        )
        return files

    @staticmethod
    def get_data(process_model_info: ProcessModelInfo, file_name: str) -> bytes:
        full_file_path = FileSystemService.full_file_path(process_model_info, file_name)
        if not os.path.exists(full_file_path):
            raise ProcessModelFileNotFoundError(f"No file found with name {file_name} in {process_model_info.display_name}")
        with open(full_file_path, "rb") as f_handle:
            spec_file_data = f_handle.read()
        return spec_file_data

    @staticmethod
    def full_file_path(process_model: ProcessModelInfo, file_name: str) -> str:
        return os.path.abspath(os.path.join(FileSystemService.process_model_full_path(process_model), file_name))

    @staticmethod
    def full_path_from_relative_path(relative_path: str) -> str:
        return os.path.join(FileSystemService.root_path(), relative_path)

    @classmethod
    def file_exists_at_relative_path(cls, relative_path: str, file_name: str) -> bool:
        full_path = cls.full_path_from_relative_path(os.path.join(relative_path, file_name))
        return os.path.isfile(full_path)

    @classmethod
    def contents_of_file_at_relative_path(cls, relative_path: str, file_name: str) -> str:
        full_path = cls.full_path_from_relative_path(os.path.join(relative_path, file_name))
        with open(full_path) as f:
            return f.read()

    @classmethod
    def contents_of_json_file_at_relative_path(cls, relative_path: str, file_name: str) -> Any:
        contents = cls.contents_of_file_at_relative_path(relative_path, file_name)
        return json.loads(contents)

    @classmethod
    def write_to_file_at_relative_path(cls, relative_path: str, file_name: str, contents: str) -> None:
        full_path = cls.full_path_from_relative_path(os.path.join(relative_path, file_name))
        with open(full_path, "w") as f:
            f.write(contents)

    @classmethod
    def write_to_json_file_at_relative_path(cls, relative_path: str, file_name: str, contents: Any) -> None:
        cls.write_to_file_at_relative_path(relative_path, file_name, json.dumps(contents, indent=4, sort_keys=True))

    @staticmethod
    def process_model_relative_path(process_model: ProcessModelInfo) -> str:
        """Get the file path to a process model relative to SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR.

        If the full path is /path/to/process-group-a/group-b/process-model-a, it will return:
        process-group-a/group-b/process-model-a
        """
        workflow_path = FileSystemService.process_model_full_path(process_model)
        return os.path.relpath(workflow_path, start=FileSystemService.root_path())

    @classmethod
    def relative_location(cls, path: str) -> str:
        return os.path.dirname(os.path.relpath(path, start=FileSystemService.root_path()))

    @staticmethod
    def process_group_path_for_spec(process_model: ProcessModelInfo) -> str:
        # os.path.split apparently returns 2 element tulple like: (first/path, last_item)
        process_group_id, _ = os.path.split(process_model.id_for_file_path())
        return FileSystemService.full_path_from_id(process_group_id)

    @classmethod
    def process_model_full_path(cls, process_model: ProcessModelInfo) -> str:
        return cls.full_path_from_id(process_model.id)

    @staticmethod
    def full_path_to_process_model_file(process_model: ProcessModelInfo) -> str:
        return os.path.join(
            FileSystemService.process_model_full_path(process_model),
            process_model.primary_file_name,  # type: ignore
        )

    def next_display_order(self, process_model: ProcessModelInfo) -> int:
        path = self.process_group_path_for_spec(process_model)
        if os.path.exists(path):
            return len(next(os.walk(path))[1])
        else:
            return 0

    @staticmethod
    def write_file_data_to_system(file_path: str, file_data: bytes) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f_handle:
            f_handle.write(file_data)

    @staticmethod
    def get_extension(file_name: str) -> str:
        _, file_extension = os.path.splitext(file_name)
        return file_extension.lower().strip()[1:]

    @staticmethod
    def assert_valid_file_name(file_name: str) -> None:
        file_extension = FileSystemService.get_extension(file_name)
        if file_extension not in FileType.list():
            raise ApiError(
                "unknown_extension",
                "The file you provided does not have an accepted extension:" + file_extension,
                status_code=404,
            )

    @staticmethod
    def _timestamp(file_path: str) -> float:
        return os.path.getmtime(file_path)

    @staticmethod
    def _last_modified(file_path: str) -> datetime:
        # Returns the last modified date of the given file.
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp, timezone.utc)

    @staticmethod
    def file_type(file_name: str) -> FileType:
        extension = FileSystemService.get_extension(file_name)
        return FileType[extension]

    @staticmethod
    def _get_files(file_path: str, file_name: str | None = None) -> list[File]:
        """Returns an array of File objects at the given path, can be restricted to just one file."""
        files = []
        items = os.scandir(file_path)
        for item in items:
            if item.is_file():
                if item.name.startswith("."):
                    continue  # Ignore hidden files
                if item.name == FileSystemService.PROCESS_MODEL_JSON_FILE:
                    continue  # Ignore the json files.
                if file_name is not None and item.name != file_name:
                    continue
                file = FileSystemService.to_file_object_from_dir_entry(item)
                files.append(file)
        return files

    @staticmethod
    def to_file_object(file_name: str, file_path: str) -> File:
        file_type = FileSystemService.file_type(file_name)
        content_type = CONTENT_TYPES[file_type.name]
        last_modified = FileSystemService._last_modified(file_path)
        size = os.path.getsize(file_path)
        file = File.from_file_system(file_name, file_type, content_type, last_modified, size)
        return file

    @staticmethod
    def to_file_object_from_dir_entry(item: os.DirEntry) -> File:
        extension = FileSystemService.get_extension(item.name)
        try:
            file_type = FileType[extension]
            content_type = CONTENT_TYPES[file_type.name]
        except KeyError as exception:
            raise ApiError(
                "invalid_type",
                f"Invalid File Type: {extension}, for file {item.name}",
            ) from exception
        stats = item.stat()
        file_size = stats.st_size
        last_modified = FileSystemService._last_modified(item.path)
        return File.from_file_system(item.name, file_type, content_type, last_modified, file_size)
