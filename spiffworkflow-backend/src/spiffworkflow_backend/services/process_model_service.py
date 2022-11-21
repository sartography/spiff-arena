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
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.process_group import ProcessGroupSchema
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.process_model import ProcessModelInfoSchema
from spiffworkflow_backend.services.file_system_service import FileSystemService

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

    def is_group(self, path: str) -> bool:
        """Is_group."""
        group_json_path = os.path.join(path, self.PROCESS_GROUP_JSON_FILE)
        if os.path.exists(group_json_path):
            return True
        return False

    def is_model(self, path: str) -> bool:
        """Is_model."""
        model_json_path = os.path.join(path, self.PROCESS_MODEL_JSON_FILE)
        if os.path.exists(model_json_path):
            return True
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

    def add_process_model(self, process_model: ProcessModelInfo) -> None:
        """Add_spec."""
        display_order = self.next_display_order(process_model)
        process_model.display_order = display_order
        self.save_process_model(process_model)

    def update_process_model(
        self, process_model: ProcessModelInfo, attributes_to_update: dict
    ) -> None:
        """Update_spec."""
        for atu_key, atu_value in attributes_to_update.items():
            if hasattr(process_model, atu_key):
                setattr(process_model, atu_key, atu_value)
        self.save_process_model(process_model)

    def save_process_model(self, process_model: ProcessModelInfo) -> None:
        """Save_process_model."""
        process_model_path = os.path.abspath(
            os.path.join(FileSystemService.root_path(), process_model.id)
        )
        os.makedirs(process_model_path, exist_ok=True)
        json_path = os.path.abspath(
            os.path.join(process_model_path, self.PROCESS_MODEL_JSON_FILE)
        )
        process_model_id = process_model.id
        # we don't save id in the json file
        # this allows us to move models around on the filesystem
        # the id is determined by its location on the filesystem
        delattr(process_model, "id")
        json_data = self.PROCESS_MODEL_SCHEMA.dump(process_model)
        self.write_json_file(json_path, json_data)
        process_model.id = process_model_id

    def process_model_delete(self, process_model_id: str) -> None:
        """Delete Procecss Model."""
        instances = ProcessInstanceModel.query.filter(
            ProcessInstanceModel.process_model_identifier == process_model_id
        ).all()
        if len(instances) > 0:
            raise ApiError(
                error_code="existing_instances",
                message=f"We cannot delete the model `{process_model_id}`, there are existing instances that depend on it.",
            )
        self.get_process_model(process_model_id)
        # path = self.workflow_path(process_model)
        path = f"{FileSystemService.root_path()}/{process_model_id}"
        shutil.rmtree(path)

    @classmethod
    def get_process_model_from_relative_path(
        cls, relative_path: str
    ) -> ProcessModelInfo:
        """Get_process_model_from_relative_path."""
        process_group_identifier, _ = os.path.split(relative_path)
        process_group = cls().get_process_group(process_group_identifier)
        path = os.path.join(FileSystemService.root_path(), relative_path)
        return cls().__scan_process_model(path, process_group=process_group)

    def get_process_model(self, process_model_id: str) -> ProcessModelInfo:
        """Get a process model from a model and group id.

        process_model_id is the full path to the model--including groups.
        """
        if not os.path.exists(FileSystemService.root_path()):
            raise ProcessEntityNotFoundError("process_model_root_not_found")

        model_path = os.path.abspath(
            os.path.join(FileSystemService.root_path(), process_model_id)
        )
        if self.is_model(model_path):
            process_model = self.get_process_model_from_relative_path(process_model_id)
            return process_model

        # group_path, model_id = os.path.split(process_model_id)
        # if group_path is not None:
        #     process_group = self.get_process_group(group_path)
        #     if process_group is not None:
        #         for process_model in process_group.process_models:
        #             if process_model_id == process_model.id:
        #                 return process_model
        # with os.scandir(FileSystemService.root_path()) as process_group_dirs:
        #     for item in process_group_dirs:
        #         process_group_dir = item
        #         if item.is_dir():
        #             with os.scandir(item.path) as spec_dirs:
        #                 for sd in spec_dirs:
        #                     if sd.name == process_model_id:
        #                         # Now we have the process_group directory, and spec directory
        #                         process_group = self.__scan_process_group(
        #                             process_group_dir
        #                         )
        #                         return self.__scan_process_model(sd.path, sd.name, process_group)
        raise ProcessEntityNotFoundError("process_model_not_found")

    def get_process_models(
        self, process_group_id: Optional[str] = None
    ) -> List[ProcessModelInfo]:
        """Get process models."""
        process_models = []
        root_path = FileSystemService.root_path()
        if process_group_id:
            awesome_id = process_group_id.replace("/", os.sep)
            root_path = os.path.join(root_path, awesome_id)
        process_model_glob = os.path.join(root_path, "**", "process_model.json")
        for file in glob(process_model_glob, recursive=True):
            process_model_relative_path = os.path.relpath(
                file, start=FileSystemService.root_path()
            )
            process_model = self.get_process_model_from_relative_path(
                os.path.dirname(process_model_relative_path)
            )
            process_models.append(process_model)
        process_models.sort()
        return process_models

    def get_process_groups(
        self, process_group_id: Optional[str] = None
    ) -> list[ProcessGroup]:
        """Returns the process_groups as a list in display order."""
        process_groups = self.__scan_process_groups(process_group_id)
        process_groups.sort()
        return process_groups

    def get_process_group(self, process_group_id: str) -> ProcessGroup:
        """Look for a given process_group, and return it."""
        if os.path.exists(FileSystemService.root_path()):
            process_group_path = os.path.abspath(
                os.path.join(FileSystemService.root_path(), process_group_id)
            )
            if self.is_group(process_group_path):
                return self.__scan_process_group(process_group_path)
                # nested_groups = []
                # process_group_dir = os.scandir(process_group_path)
                # for item in process_group_dir:
                #     if self.is_group(item.path):
                #         nested_group = self.get_process_group(os.path.join(process_group_path, item.path))
                #         nested_groups.append(nested_group)
                #     elif self.is_model(item.path):
                #         print("get_process_group: ")
                #         return self.__scan_process_group(process_group_path)
            # with os.scandir(FileSystemService.root_path()) as directory_items:
            #     for item in directory_items:
            #         if item.is_dir() and item.name == process_group_id:
            #             return self.__scan_process_group(item)

        raise ProcessEntityNotFoundError(
            "process_group_not_found", f"Process Group Id: {process_group_id}"
        )

    def add_process_group(self, process_group: ProcessGroup) -> ProcessGroup:
        """Add_process_group."""
        display_order = len(self.get_process_groups())
        process_group.display_order = display_order
        return self.update_process_group(process_group)

    def update_process_group(self, process_group: ProcessGroup) -> ProcessGroup:
        """Update_process_group."""
        cat_path = self.process_group_path(process_group.id)
        os.makedirs(cat_path, exist_ok=True)
        json_path = os.path.join(cat_path, self.PROCESS_GROUP_JSON_FILE)
        serialized_process_group = process_group.serialized
        # we don't store `id` in the json files
        # this allows us to move groups around on the filesystem
        del serialized_process_group["id"]
        self.write_json_file(json_path, serialized_process_group)
        return process_group

    def __get_all_nested_models(self, group_path: str) -> list:
        """__get_all_nested_models."""
        all_nested_models = []
        for _root, dirs, _files in os.walk(group_path):
            for dir in dirs:
                model_dir = os.path.join(group_path, dir)
                if ProcessModelService().is_model(model_dir):
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
                    message=f"We cannot delete the group `{process_group_id}`, "
                    f"there are models with existing instances inside the group. {problem_models}",
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

    def __scan_process_groups(
        self, process_group_id: Optional[str] = None
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
                if item.is_dir() and self.is_group(item):  # type: ignore
                    scanned_process_group = self.__scan_process_group(item.path)
                    process_groups.append(scanned_process_group)
            return process_groups

    def __scan_process_group(self, dir_path: str) -> ProcessGroup:
        """Reads the process_group.json file, and any nested directories."""
        cat_path = os.path.join(dir_path, self.PROCESS_GROUP_JSON_FILE)
        if os.path.exists(cat_path):
            with open(cat_path) as cat_json:
                data = json.load(cat_json)
                # we don't store `id` in the json files, so we add it back in here
                relative_path = os.path.relpath(dir_path, FileSystemService.root_path())
                data["id"] = relative_path
                process_group = ProcessGroup(**data)
                if process_group is None:
                    raise ApiError(
                        error_code="process_group_could_not_be_loaded_from_disk",
                        message=f"We could not load the process_group from disk from: {dir_path}",
                    )
        else:
            process_group_id = dir_path.replace(FileSystemService.root_path(), "")
            process_group = ProcessGroup(
                id="",
                display_name=process_group_id,
                display_order=10000,
                admin=False,
            )
            self.write_json_file(cat_path, self.GROUP_SCHEMA.dump(process_group))
            # we don't store `id` in the json files, so we add it in here
            process_group.id = process_group_id
        with os.scandir(dir_path) as nested_items:
            process_group.process_models = []
            process_group.process_groups = []
            for nested_item in nested_items:
                if nested_item.is_dir():
                    # TODO: check whether this is a group or model
                    if self.is_group(nested_item.path):
                        # This is a nested group
                        process_group.process_groups.append(
                            self.__scan_process_group(nested_item.path)
                        )
                    elif self.is_model(nested_item.path):
                        process_group.process_models.append(
                            self.__scan_process_model(
                                nested_item.path,
                                nested_item.name,
                                process_group=process_group,
                            )
                        )
            process_group.process_models.sort()
            # process_group.process_groups.sort()
        return process_group

    def __scan_process_model(
        self,
        path: str,
        name: Optional[str] = None,
        process_group: Optional[ProcessGroup] = None,
    ) -> ProcessModelInfo:
        """__scan_process_model."""
        json_file_path = os.path.join(path, self.PROCESS_MODEL_JSON_FILE)

        if os.path.exists(json_file_path):
            with open(json_file_path) as wf_json:
                data = json.load(wf_json)
                if "process_group_id" in data:
                    data.pop("process_group_id")
                # we don't save `id` in the json file, so we add it back in here.
                relative_path = os.path.relpath(path, FileSystemService.root_path())
                data["id"] = relative_path
                process_model_info = ProcessModelInfo(**data)
                if process_model_info is None:
                    raise ApiError(
                        error_code="process_model_could_not_be_loaded_from_disk",
                        message=f"We could not load the process_model from disk with data: {data}",
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
                is_review=False,
            )
            self.write_json_file(
                json_file_path, self.PROCESS_MODEL_SCHEMA.dump(process_model_info)
            )
            # we don't store `id` in the json files, so we add it in here
            process_model_info.id = name
        if process_group:
            process_model_info.process_group = process_group.id
        return process_model_info
