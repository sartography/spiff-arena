"""Process_model_service."""
import json
import os
import shutil
from glob import glob
from typing import Any
from typing import List
from typing import Optional
from typing import TypeVar

from flask_bpmn.api.api_error import ApiError

from spiffworkflow_backend.exceptions.process_entity_not_found_error import (
    ProcessEntityNotFoundError,
)
from spiffworkflow_backend.interfaces import ProcessGroupLite
from spiffworkflow_backend.interfaces import ProcessGroupLitesWithCache
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.process_group import ProcessGroupSchema
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.process_model import ProcessModelInfoSchema
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.user_service import UserService

T = TypeVar("T")


class ProcessModelService(FileSystemService):
    """ProcessModelService."""

    """This is a way of persisting json files to the file system in a way that mimics the data
    as it would have been stored in the database. This is specific to Workflow Specifications, and
    Workflow Specification process_groups.
    We do this, so we can easily drop in a new configuration on the file system, and change all
    the workflow process_models at once, or manage those file in a git repository. """

    GROUP_SCHEMA = ProcessGroupSchema()
    PROCESS_MODEL_SCHEMA = ProcessModelInfoSchema()

    @classmethod
    def path_to_id(cls, path: str) -> str:
        """Replace the os path separator for the standard id separator."""
        return path.replace(os.sep, '/')

    @classmethod
    def is_group(cls, path: str) -> bool:
        """Is_group."""
        group_json_path = os.path.join(path, cls.PROCESS_GROUP_JSON_FILE)
        if os.path.exists(group_json_path):
            return True
        return False

    @classmethod
    def is_group_identifier(cls, process_group_identifier: str) -> bool:
        """Is_group_identifier."""
        if os.path.exists(FileSystemService.root_path()):
            process_group_path = os.path.abspath(
                os.path.join(
                    FileSystemService.root_path(),
                    FileSystemService.id_string_to_relative_path(
                        process_group_identifier
                    ),
                )
            )
            return cls.is_group(process_group_path)

        return False

    @classmethod
    def is_model(cls, path: str) -> bool:
        """Is_model."""
        model_json_path = os.path.join(path, cls.PROCESS_MODEL_JSON_FILE)
        if os.path.exists(model_json_path):
            return True
        return False

    @classmethod
    def is_model_identifier(cls, process_model_identifier: str) -> bool:
        """Is_model_identifier."""
        if os.path.exists(FileSystemService.root_path()):
            process_model_path = os.path.abspath(
                os.path.join(
                    FileSystemService.root_path(),
                    FileSystemService.id_string_to_relative_path(
                        process_model_identifier
                    ),
                )
            )
            return cls.is_model(process_model_path)

        return False

    @staticmethod
    def write_json_file(
        file_path: str, json_data: dict, indent: int = 4, sort_keys: bool = True
    ) -> None:
        """Write json file."""
        with open(file_path, "w") as h_open:
            json.dump(json_data, h_open, indent=indent, sort_keys=sort_keys)

    @staticmethod
    def get_batch(
        items: list[T],
        page: int = 1,
        per_page: int = 10,
    ) -> list[T]:
        """Get_batch."""
        start = (page - 1) * per_page
        end = start + per_page
        return items[start:end]

    @classmethod
    def add_process_model(cls, process_model: ProcessModelInfo) -> None:
        """Add_spec."""
        cls.save_process_model(process_model)

    @classmethod
    def update_process_model(
        cls, process_model: ProcessModelInfo, attributes_to_update: dict
    ) -> None:
        """Update_spec."""
        for atu_key, atu_value in attributes_to_update.items():
            if hasattr(process_model, atu_key):
                setattr(process_model, atu_key, atu_value)
        cls.save_process_model(process_model)

    @classmethod
    def save_process_model(cls, process_model: ProcessModelInfo) -> None:
        """Save_process_model."""
        process_model_path = os.path.abspath(
            os.path.join(FileSystemService.root_path(), process_model.id)
        )
        os.makedirs(process_model_path, exist_ok=True)
        json_path = os.path.abspath(
            os.path.join(process_model_path, cls.PROCESS_MODEL_JSON_FILE)
        )
        process_model_id = process_model.id
        # we don't save id in the json file
        # this allows us to move models around on the filesystem
        # the id is determined by its location on the filesystem
        delattr(process_model, "id")
        json_data = cls.PROCESS_MODEL_SCHEMA.dump(process_model)
        cls.write_json_file(json_path, json_data)
        process_model.id = process_model_id

    def process_model_delete(self, process_model_id: str) -> None:
        """Delete Procecss Model."""
        instances = ProcessInstanceModel.query.filter(
            ProcessInstanceModel.process_model_identifier == process_model_id
        ).all()
        if len(instances) > 0:
            raise ApiError(
                error_code="existing_instances",
                message=(
                    f"We cannot delete the model `{process_model_id}`, there are"
                    " existing instances that depend on it."
                ),
            )
        process_model = self.get_process_model(process_model_id)
        path = self.workflow_path(process_model)
        shutil.rmtree(path)

    def process_model_move(
        self, original_process_model_id: str, new_location: str
    ) -> ProcessModelInfo:
        """Process_model_move."""
        process_model = self.get_process_model(original_process_model_id)
        original_model_path = self.workflow_path(process_model)
        _, model_id = os.path.split(original_model_path)
        new_relative_path = os.path.join(new_location, model_id)
        new_model_path = os.path.abspath(
            os.path.join(FileSystemService.root_path(), new_relative_path)
        )
        shutil.move(original_model_path, new_model_path)
        new_process_model = self.get_process_model(new_relative_path)
        return new_process_model

    @classmethod
    def get_process_model_from_relative_path(
        cls, relative_path: str
    ) -> ProcessModelInfo:
        """Get_process_model_from_relative_path."""
        path = os.path.join(FileSystemService.root_path(), relative_path)
        return cls.__scan_process_model(path)

    @classmethod
    def get_process_model(cls, process_model_id: str) -> ProcessModelInfo:
        """Get a process model from a model and group id.

        process_model_id is the full path to the model--including groups.
        """
        if not os.path.exists(FileSystemService.root_path()):
            raise ProcessEntityNotFoundError("process_model_root_not_found")

        model_path = os.path.abspath(
            os.path.join(FileSystemService.root_path(), process_model_id)
        )
        if cls.is_model(model_path):
            return cls.get_process_model_from_relative_path(process_model_id)
        raise ProcessEntityNotFoundError("process_model_not_found")

    @classmethod
    def get_process_models(
        cls,
        process_group_id: Optional[str] = None,
        recursive: Optional[bool] = False,
        filter_runnable_by_user: Optional[bool] = False,
    ) -> List[ProcessModelInfo]:
        """Get process models."""
        process_models = []
        root_path = FileSystemService.root_path()
        if process_group_id:
            awesome_id = process_group_id.replace("/", os.sep)
            root_path = os.path.join(root_path, awesome_id)

        process_model_glob = os.path.join(root_path, "*", "process_model.json")
        if recursive:
            process_model_glob = os.path.join(root_path, "**", "process_model.json")

        for file in glob(process_model_glob, recursive=True):
            process_model_relative_path = os.path.relpath(
                file, start=FileSystemService.root_path()
            )
            process_model = cls.get_process_model_from_relative_path(
                os.path.dirname(process_model_relative_path)
            )
            process_models.append(process_model)
        process_models.sort()

        if filter_runnable_by_user:
            user = UserService.current_user()
            new_process_model_list = []
            for process_model in process_models:
                modified_process_model_id = ProcessModelInfo.modify_process_identifier_for_path_param(process_model.id)
                uri = f"/v1.0/process-instances/{modified_process_model_id}"
                has_permission = AuthorizationService.user_has_permission(
                    user=user, permission="create", target_uri=uri
                )
                if has_permission:
                    new_process_model_list.append(process_model)
            return new_process_model_list

        return process_models

    @classmethod
    def get_parent_group_array_and_cache_it(
        cls, process_identifier: str, process_group_cache: dict[str, ProcessGroup]
    ) -> ProcessGroupLitesWithCache:
        """Get_parent_group_array."""
        full_group_id_path = None
        parent_group_array: list[ProcessGroupLite] = []
        for process_group_id_segment in process_identifier.split("/")[0:-1]:
            if full_group_id_path is None:
                full_group_id_path = process_group_id_segment
            else:
                full_group_id_path = os.path.join(full_group_id_path, process_group_id_segment)  # type: ignore
            parent_group = process_group_cache.get(full_group_id_path, None)
            if parent_group is None:
                parent_group = ProcessModelService.get_process_group(full_group_id_path)

            if parent_group:
                if full_group_id_path not in process_group_cache:
                    process_group_cache[full_group_id_path] = parent_group
                parent_group_array.append(
                    {"id": parent_group.id, "display_name": parent_group.display_name}
                )
        return {"cache": process_group_cache, "process_groups": parent_group_array}

    @classmethod
    def get_parent_group_array(cls, process_identifier: str) -> list[ProcessGroupLite]:
        """Get_parent_group_array."""
        parent_group_lites_with_cache = cls.get_parent_group_array_and_cache_it(
            process_identifier, {}
        )
        return parent_group_lites_with_cache["process_groups"]

    @classmethod
    def get_process_groups(
        cls, process_group_id: Optional[str] = None
    ) -> list[ProcessGroup]:
        """Returns the process_groups."""
        process_groups = cls.__scan_process_groups(process_group_id)
        process_groups.sort()
        return process_groups

    @classmethod
    def get_process_group(
        cls, process_group_id: str, find_direct_nested_items: bool = True
    ) -> ProcessGroup:
        """Look for a given process_group, and return it."""
        if os.path.exists(FileSystemService.root_path()):
            process_group_path = os.path.abspath(
                os.path.join(
                    FileSystemService.root_path(),
                    FileSystemService.id_string_to_relative_path(process_group_id),
                )
            )
            if cls.is_group(process_group_path):
                return cls.find_or_create_process_group(
                    process_group_path,
                    find_direct_nested_items=find_direct_nested_items,
                )

        raise ProcessEntityNotFoundError(
            "process_group_not_found", f"Process Group Id: {process_group_id}"
        )

    @classmethod
    def add_process_group(cls, process_group: ProcessGroup) -> ProcessGroup:
        """Add_process_group."""
        return cls.update_process_group(process_group)

    @classmethod
    def update_process_group(cls, process_group: ProcessGroup) -> ProcessGroup:
        """Update_process_group."""
        cat_path = cls.process_group_path(process_group.id)
        os.makedirs(cat_path, exist_ok=True)
        json_path = os.path.join(cat_path, cls.PROCESS_GROUP_JSON_FILE)
        serialized_process_group = process_group.serialized
        # we don't store `id` in the json files
        # this allows us to move groups around on the filesystem
        del serialized_process_group["id"]
        cls.write_json_file(json_path, serialized_process_group)
        return process_group

    def process_group_move(
        self, original_process_group_id: str, new_location: str
    ) -> ProcessGroup:
        """Process_group_move."""
        original_group_path = self.process_group_path(original_process_group_id)
        _, original_group_id = os.path.split(original_group_path)
        new_root = os.path.join(FileSystemService.root_path(), new_location)
        new_group_path = os.path.abspath(
            os.path.join(FileSystemService.root_path(), new_root, original_group_id)
        )
        destination = shutil.move(original_group_path, new_group_path)
        new_process_group = self.get_process_group(destination)
        return new_process_group

    def __get_all_nested_models(self, group_path: str) -> list:
        """__get_all_nested_models."""
        all_nested_models = []
        for _root, dirs, _files in os.walk(group_path):
            for dir in dirs:
                model_dir = os.path.join(group_path, dir)
                if ProcessModelService.is_model(model_dir):
                    process_model = self.get_process_model(model_dir)
                    all_nested_models.append(process_model)
        return all_nested_models

    def process_group_delete(self, process_group_id: str) -> None:
        """Delete_process_group."""
        problem_models = []
        path = self.process_group_path(process_group_id)
        if os.path.exists(path):
            nested_models = self.__get_all_nested_models(path)
            for process_model in nested_models:
                instances = ProcessInstanceModel.query.filter(
                    ProcessInstanceModel.process_model_identifier == process_model.id
                ).all()
                if len(instances) > 0:
                    problem_models.append(process_model)
            if len(problem_models) > 0:
                raise ApiError(
                    error_code="existing_instances",
                    message=(
                        f"We cannot delete the group `{process_group_id}`, there are"
                        " models with existing instances inside the group."
                        f" {problem_models}"
                    ),
                )
            shutil.rmtree(path)
        self.cleanup_process_group_display_order()

    def cleanup_process_group_display_order(self) -> List[Any]:
        """Cleanup_process_group_display_order."""
        process_groups = self.get_process_groups()  # Returns an ordered list
        index = 0
        for process_group in process_groups:
            process_group.display_order = index
            self.update_process_group(process_group)
            index += 1
        return process_groups

    @classmethod
    def __scan_process_groups(
        cls, process_group_id: Optional[str] = None
    ) -> list[ProcessGroup]:
        """__scan_process_groups."""
        if not os.path.exists(FileSystemService.root_path()):
            return []  # Nothing to scan yet.  There are no files.
        if process_group_id is not None:
            scan_path = os.path.join(FileSystemService.root_path(), process_group_id)
        else:
            scan_path = FileSystemService.root_path()

        with os.scandir(scan_path) as directory_items:
            process_groups = []
            for item in directory_items:
                # if item.is_dir() and not item.name[0] == ".":
                if item.is_dir() and cls.is_group(item):  # type: ignore
                    scanned_process_group = cls.find_or_create_process_group(item.path)
                    process_groups.append(scanned_process_group)
            return process_groups

    @classmethod
    def find_or_create_process_group(
        cls, dir_path: str, find_direct_nested_items: bool = True
    ) -> ProcessGroup:
        """Reads the process_group.json file, and any nested directories."""
        cat_path = os.path.join(dir_path, cls.PROCESS_GROUP_JSON_FILE)
        if os.path.exists(cat_path):
            with open(cat_path) as cat_json:
                data = json.load(cat_json)
                # we don't store `id` in the json files, so we add it back in here
                relative_path = os.path.relpath(dir_path, FileSystemService.root_path())
                data["id"] = cls.path_to_id(relative_path)
                process_group = ProcessGroup(**data)
                if process_group is None:
                    raise ApiError(
                        error_code="process_group_could_not_be_loaded_from_disk",
                        message=(
                            "We could not load the process_group from disk from:"
                            f" {dir_path}"
                        ),
                    )
        else:
            process_group_id = cls.path_to_id(dir_path.replace(FileSystemService.root_path(), ""))
            process_group = ProcessGroup(
                id="",
                display_name=process_group_id,
                display_order=10000,
                admin=False,
            )
            cls.write_json_file(cat_path, cls.GROUP_SCHEMA.dump(process_group))
            # we don't store `id` in the json files, so we add it in here
            process_group.id = process_group_id

        if find_direct_nested_items:
            with os.scandir(dir_path) as nested_items:
                process_group.process_models = []
                process_group.process_groups = []
                for nested_item in nested_items:
                    if nested_item.is_dir():
                        # TODO: check whether this is a group or model
                        if cls.is_group(nested_item.path):
                            # This is a nested group
                            process_group.process_groups.append(
                                cls.find_or_create_process_group(nested_item.path)
                            )
                        elif ProcessModelService.is_model(nested_item.path):
                            process_group.process_models.append(
                                cls.__scan_process_model(
                                    nested_item.path,
                                    nested_item.name,
                                )
                            )
                process_group.process_models.sort()
                # process_group.process_groups.sort()
        return process_group

    # path might have backslashes on windows, not sure
    # not sure if os.path.join converts forward slashes in the relative_path argument to backslashes:
    #   path = os.path.join(FileSystemService.root_path(), relative_path)
    @classmethod
    def __scan_process_model(
        cls,
        path: str,
        name: Optional[str] = None,
    ) -> ProcessModelInfo:
        """__scan_process_model."""
        json_file_path = os.path.join(path, cls.PROCESS_MODEL_JSON_FILE)

        if os.path.exists(json_file_path):
            with open(json_file_path) as wf_json:
                data = json.load(wf_json)
                if "process_group_id" in data:
                    data.pop("process_group_id")
                # we don't save `id` in the json file, so we add it back in here.
                relative_path = os.path.relpath(path, FileSystemService.root_path())
                data["id"] = cls.path_to_id(relative_path)
                process_model_info = ProcessModelInfo(**data)
                if process_model_info is None:
                    raise ApiError(
                        error_code="process_model_could_not_be_loaded_from_disk",
                        message=(
                            "We could not load the process_model from disk with data:"
                            f" {data}"
                        ),
                    )
        else:
            if name is None:
                raise ApiError(
                    error_code="missing_name_of_process_model",
                    message="Missing name of process model. It should be given",
                )

            process_model_info = ProcessModelInfo(
                id="",
                display_name=name,
                description="",
                display_order=0,
            )
            cls.write_json_file(
                json_file_path, cls.PROCESS_MODEL_SCHEMA.dump(process_model_info)
            )
            # we don't store `id` in the json files, so we add it in here
            process_model_info.id = name
        return process_model_info
