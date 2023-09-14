import os
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime

import pytz
from flask import current_app
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.file import CONTENT_TYPES
from spiffworkflow_backend.models.file import File
from spiffworkflow_backend.models.file import FileType
from spiffworkflow_backend.models.process_model import ProcessModelInfo


class ProcessModelFileNotFoundError(Exception):
    pass


class FileSystemService:

    """Simple Service meant for extension that provides some useful
    methods for dealing with the File system.
    """

    PROCESS_GROUP_JSON_FILE = "process_group.json"
    PROCESS_MODEL_JSON_FILE = "process_model.json"

    # https://stackoverflow.com/a/24176022/6090676
    @staticmethod
    @contextmanager
    def cd(newdir: str) -> Generator:
        prevdir = os.getcwd()
        os.chdir(os.path.expanduser(newdir))
        try:
            yield
        finally:
            os.chdir(prevdir)

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
            raise ProcessModelFileNotFoundError(
                f"No file found with name {file_name} in {process_model_info.display_name}"
            )
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
    
    @staticmethod
    def process_model_relative_path(process_model: ProcessModelInfo) -> str:
        """Get the file path to a process model relative to SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR.

        If the full path is /path/to/process-group-a/group-b/process-model-a, it will return:
        process-group-a/group-b/process-model-a
        """
        workflow_path = FileSystemService.process_model_full_path(process_model)
        return os.path.relpath(workflow_path, start=FileSystemService.root_path())

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
            FileSystemService.process_model_full_path(process_model), process_model.primary_file_name  # type: ignore
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
        utc_dt = datetime.utcfromtimestamp(timestamp)
        aware_utc_dt = utc_dt.replace(tzinfo=pytz.utc)
        return aware_utc_dt

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
