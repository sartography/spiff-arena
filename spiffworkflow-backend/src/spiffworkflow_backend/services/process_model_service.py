import json
import os
import shutil
import uuid
from json import JSONDecodeError
from typing import Any
from typing import TypeVar

from flask import current_app

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.exceptions.process_entity_not_found_error import ProcessEntityNotFoundError
from spiffworkflow_backend.interfaces import ProcessGroupLite
from spiffworkflow_backend.interfaces import ProcessGroupLitesWithCache
from spiffworkflow_backend.models.permission_assignment import PermitDeny
from spiffworkflow_backend.models.process_group import PROCESS_GROUP_SUPPORTED_KEYS_FOR_DISK_SERIALIZATION
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.process_group import ProcessGroupSchema
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_model import PROCESS_MODEL_SUPPORTED_KEYS_FOR_DISK_SERIALIZATION
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.process_model import ProcessModelInfoSchema
from spiffworkflow_backend.models.reference_cache import Reference
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.user_service import UserService

T = TypeVar("T")


class ProcessModelWithInstancesNotDeletableError(Exception):
    pass


class ProcessModelService(FileSystemService):
    """This is a way of persisting json files to the file system in a way that mimics the data
    as it would have been stored in the database. This is specific to Workflow Specifications, and
    Workflow Specification process_groups.
    We do this, so we can easily drop in a new configuration on the file system, and change all
    the workflow process_models at once, or manage those file in a git repository."""

    GROUP_SCHEMA = ProcessGroupSchema()
    PROCESS_MODEL_SCHEMA = ProcessModelInfoSchema()

    @classmethod
    def path_to_id(cls, path: str) -> str:
        """Replace the os path separator for the standard id separator."""
        return path.replace(os.sep, "/")

    @classmethod
    def is_process_group(cls, path: str) -> bool:
        group_json_path = os.path.join(path, cls.PROCESS_GROUP_JSON_FILE)
        if os.path.exists(group_json_path):
            return True
        return False

    @classmethod
    def is_process_group_identifier(cls, process_group_identifier: str) -> bool:
        if os.path.exists(FileSystemService.root_path()):
            process_group_path = FileSystemService.full_path_from_id(process_group_identifier)
            return cls.is_process_group(process_group_path)

        return False

    @classmethod
    def is_process_model(cls, path: str) -> bool:
        model_json_path = os.path.join(path, cls.PROCESS_MODEL_JSON_FILE)
        if os.path.exists(model_json_path):
            return True
        return False

    @classmethod
    def is_process_model_identifier(cls, process_model_identifier: str) -> bool:
        if os.path.exists(FileSystemService.root_path()):
            process_model_path = FileSystemService.full_path_from_id(process_model_identifier)
            return cls.is_process_model(process_model_path)

        return False

    @staticmethod
    def write_json_file(file_path: str, json_data: dict, indent: int = 4, sort_keys: bool = True) -> None:
        with open(file_path, "w") as h_open:
            json.dump(json_data, h_open, indent=indent, sort_keys=sort_keys)

    @staticmethod
    def get_batch(
        items: list[T],
        page: int = 1,
        per_page: int = 10,
    ) -> list[T]:
        start = (page - 1) * per_page
        end = start + per_page
        return items[start:end]

    @classmethod
    def add_process_model(cls, process_model: ProcessModelInfo) -> None:
        cls.save_process_model(process_model)

    @classmethod
    def update_process_model(cls, process_model: ProcessModelInfo, attributes_to_update: dict) -> None:
        for atu_key, atu_value in attributes_to_update.items():
            if hasattr(process_model, atu_key):
                setattr(process_model, atu_key, atu_value)
        cls.save_process_model(process_model)

    @classmethod
    def is_allowed_to_run_as_extension(cls, process_model: ProcessModelInfo) -> bool:
        if not current_app.config["SPIFFWORKFLOW_BACKEND_EXTENSIONS_API_ENABLED"]:
            return False

        configured_prefix = current_app.config["SPIFFWORKFLOW_BACKEND_EXTENSIONS_PROCESS_MODEL_PREFIX"]
        return process_model.id.startswith(f"{configured_prefix}/")

    @classmethod
    def add_json_data_to_json_file(cls, process_model: ProcessModelInfo, file_name: str, json_data: dict) -> None:
        full_json_data = json_data
        process_model_path = os.path.abspath(os.path.join(FileSystemService.root_path(), process_model.id_for_file_path()))
        json_path = os.path.abspath(os.path.join(process_model_path, file_name))
        if os.path.exists(json_path):
            with open(json_path) as f:
                existing_json = json.loads(f.read())
            full_json_data = {**existing_json, **json_data}
        cls.write_json_file(json_path, full_json_data)

    @classmethod
    def save_process_model(cls, process_model: ProcessModelInfo) -> None:
        process_model_path = os.path.abspath(os.path.join(FileSystemService.root_path(), process_model.id_for_file_path()))
        os.makedirs(process_model_path, exist_ok=True)
        json_path = os.path.abspath(os.path.join(process_model_path, cls.PROCESS_MODEL_JSON_FILE))
        json_data = cls.PROCESS_MODEL_SCHEMA.dump(process_model)
        for key in list(json_data.keys()):
            if key not in PROCESS_MODEL_SUPPORTED_KEYS_FOR_DISK_SERIALIZATION:
                del json_data[key]
        cls.write_json_file(json_path, json_data)

    @classmethod
    def process_model_delete(cls, process_model_id: str) -> None:
        instances = ProcessInstanceModel.query.filter(ProcessInstanceModel.process_model_identifier == process_model_id).all()
        if len(instances) > 0:
            raise ProcessModelWithInstancesNotDeletableError(
                f"We cannot delete the model `{process_model_id}`, there are existing instances that depend on it."
            )
        process_model = cls.get_process_model(process_model_id)
        path = cls.process_model_full_path(process_model)
        shutil.rmtree(path)

    @classmethod
    def process_model_move(cls, original_process_model_id: str, new_location: str) -> ProcessModelInfo:
        process_model = cls.get_process_model(original_process_model_id)
        original_model_path = cls.process_model_full_path(process_model)
        _, model_id = os.path.split(original_model_path)
        new_relative_path = os.path.join(new_location, model_id)
        new_model_path = os.path.abspath(os.path.join(FileSystemService.root_path(), new_relative_path))
        shutil.move(original_model_path, new_model_path)
        new_process_model = cls.get_process_model(new_relative_path)
        return new_process_model

    @classmethod
    def get_process_model_from_relative_path(cls, relative_path: str) -> ProcessModelInfo:
        path = os.path.join(FileSystemService.root_path(), relative_path)
        return cls.__scan_process_model(path)

    @classmethod
    def get_process_model_from_path(cls, path: str) -> ProcessModelInfo:
        relative_path = os.path.relpath(path, start=FileSystemService.root_path())
        return cls.get_process_model_from_relative_path(os.path.dirname(relative_path))

    @classmethod
    def get_process_model(cls, process_model_id: str) -> ProcessModelInfo:
        """Get a process model from a model and group id.

        process_model_id is the full path to the model--including groups.
        """
        if not os.path.exists(FileSystemService.root_path()):
            raise ProcessEntityNotFoundError("process_model_root_not_found")

        model_path = os.path.abspath(os.path.join(FileSystemService.root_path(), process_model_id))
        if cls.is_process_model(model_path):
            return cls.get_process_model_from_relative_path(process_model_id)
        raise ProcessEntityNotFoundError("process_model_not_found")

    @classmethod
    def get_process_models(
        cls,
        process_group_id: str | None = None,
        recursive: bool | None = False,
        include_files: bool | None = False,
    ) -> list[ProcessModelInfo]:
        process_models = []
        root_path = FileSystemService.root_path()
        if process_group_id:
            awesome_id = process_group_id.replace("/", os.sep)
            root_path = os.path.join(root_path, awesome_id)

        if recursive is None:
            recursive = False

        process_model_files = FileSystemService.walk_files(
            root_path,
            FileSystemService.standard_directory_predicate(recursive),
            FileSystemService.is_process_model_json_file,
        )

        for file in process_model_files:
            process_model = cls.get_process_model_from_path(file)

            if include_files:
                files = FileSystemService.get_sorted_files(process_model)
                for f in files:
                    file_contents = FileSystemService.get_data(process_model, f.name)
                    f.file_contents = file_contents
                process_model.files = files
            process_models.append(process_model)
        process_models.sort()
        return process_models

    @classmethod
    def get_process_models_for_api(
        cls,
        user: UserModel,
        process_group_id: str | None = None,
        recursive: bool | None = False,
        filter_runnable_by_user: bool | None = False,
        filter_runnable_as_extension: bool | None = False,
        include_files: bool | None = False,
    ) -> list[ProcessModelInfo]:
        if filter_runnable_as_extension and filter_runnable_by_user:
            raise Exception(
                "It is not valid to filter process models by both filter_runnable_by_user and filter_runnable_as_extension"
            )

        # get the full list (before we filter it by the ones you are allowed to start)
        process_models = cls.get_process_models(
            process_group_id=process_group_id, recursive=recursive, include_files=include_files
        )
        process_model_identifiers = [p.id for p in process_models]

        permission_to_check = "read"
        permission_base_uri = "/v1.0/process-models"
        extension_prefix = current_app.config["SPIFFWORKFLOW_BACKEND_EXTENSIONS_PROCESS_MODEL_PREFIX"]
        if filter_runnable_by_user:
            permission_to_check = "create"
            permission_base_uri = "/v1.0/process-instances"
        if filter_runnable_as_extension:
            permission_to_check = "create"
            permission_base_uri = "/v1.0/extensions"
            process_model_identifiers = [p.id.replace(f"{extension_prefix}/", "") for p in process_models]

        # these are the ones (identifiers, at least) you are allowed to start
        permitted_process_model_identifiers = cls.process_model_identifiers_with_permission_for_user(
            user=user,
            permission_to_check=permission_to_check,
            permission_base_uri=permission_base_uri,
            process_model_identifiers=process_model_identifiers,
        )

        reference_cache_processes = ReferenceCacheModel.basic_query().filter_by(type="process").all()
        process_models = cls.embellish_with_is_executable_property(process_models, reference_cache_processes)

        if filter_runnable_by_user:
            process_models = cls.filter_by_runnable(process_models, reference_cache_processes)

        permitted_process_models = []
        for process_model in process_models:
            process_model_identifier = process_model.id
            if filter_runnable_as_extension:
                process_model_identifier = process_model.id.replace(f"{extension_prefix}/", "")
            if process_model_identifier in permitted_process_model_identifiers:
                permitted_process_models.append(process_model)

        return permitted_process_models

    @classmethod
    def embellish_with_is_executable_property(
        cls, process_models: list[ProcessModelInfo], reference_cache_processes: list[ReferenceCacheModel]
    ) -> list[ProcessModelInfo]:
        for process_model in process_models:
            matching_reference_cache_process = cls.find_reference_cache_process_for_process_model(
                reference_cache_processes, process_model
            )
            if (
                matching_reference_cache_process
                and matching_reference_cache_process.properties
                and "is_executable" in matching_reference_cache_process.properties
                and matching_reference_cache_process.properties["is_executable"] is False
            ):
                process_model.is_executable = False
            else:
                process_model.is_executable = True

        return process_models

    @classmethod
    def filter_by_runnable(
        cls, process_models: list[ProcessModelInfo], reference_cache_processes: list[ReferenceCacheModel]
    ) -> list[ProcessModelInfo]:
        runnable_process_models = []
        for process_model in process_models:
            # if you want to be able to run a process model, it must have a primary file in addition to being executable
            if (
                process_model.primary_file_name is not None
                and process_model.primary_file_name != ""
                and process_model.is_executable
            ):
                runnable_process_models.append(process_model)
        return runnable_process_models

    @classmethod
    def find_reference_cache_process_for_process_model(
        cls, reference_cache_processes: list[ReferenceCacheModel], process_model: ProcessModelInfo
    ) -> ReferenceCacheModel | None:
        for reference_cache_process in reference_cache_processes:
            if (
                reference_cache_process.identifier == process_model.primary_process_id
                and reference_cache_process.file_name == process_model.primary_file_name
                and reference_cache_process.relative_location == process_model.id
            ):
                return reference_cache_process
        return None

    @classmethod
    def process_model_identifiers_with_permission_for_user(
        cls, user: UserModel, permission_to_check: str, permission_base_uri: str, process_model_identifiers: list[str]
    ) -> list[str]:
        # if user has access to uri/* with that permission then there's no reason to check each one individually
        guid_of_non_existent_item_to_check_perms_against = str(uuid.uuid4())
        has_permission = AuthorizationService.user_has_permission(
            user=user,
            permission=permission_to_check,
            target_uri=f"{permission_base_uri}/{guid_of_non_existent_item_to_check_perms_against}",
        )

        # if user has access to uri/* with that permission then there's no reason to check each one individually
        if has_permission:
            return process_model_identifiers

        permission_assignments = AuthorizationService.all_permission_assignments_for_user(user=user)

        permitted_process_model_identifiers = []
        for process_model_identifier in process_model_identifiers:
            modified_process_model_id = ProcessModelInfo.modify_process_identifier_for_path_param(process_model_identifier)
            uri = f"{permission_base_uri}/{modified_process_model_id}"
            has_permission = AuthorizationService.permission_assignments_include(
                permission_assignments=permission_assignments,
                permission=permission_to_check,
                target_uri=uri,
            )
            if has_permission:
                permitted_process_model_identifiers.append(process_model_identifier)

        return permitted_process_model_identifiers

    @classmethod
    def get_parent_group_array_and_cache_it(
        cls, process_identifier: str, process_group_cache: dict[str, ProcessGroup]
    ) -> ProcessGroupLitesWithCache:
        full_group_id_path = None
        parent_group_array: list[ProcessGroupLite] = []
        for process_group_id_segment in process_identifier.split("/")[0:-1]:
            if full_group_id_path is None:
                full_group_id_path = process_group_id_segment
            else:
                full_group_id_path = os.path.join(full_group_id_path, process_group_id_segment)  # type: ignore
            parent_group = process_group_cache.get(full_group_id_path, None)
            if parent_group is None:
                try:
                    parent_group = ProcessModelService.get_process_group(full_group_id_path)
                except ProcessEntityNotFoundError:
                    # if parent_group can no longer be found then do not add it to the cache
                    parent_group = None

            if parent_group:
                if full_group_id_path not in process_group_cache:
                    process_group_cache[full_group_id_path] = parent_group
                parent_group_array.append({"id": parent_group.id, "display_name": parent_group.display_name})
        return {"cache": process_group_cache, "process_groups": parent_group_array}

    @classmethod
    def reference_for_primary_file(cls, references: list[Reference], primary_file: str) -> Reference | None:
        for reference in references:
            if reference.file_name == primary_file:
                return reference
        return None

    @classmethod
    def get_parent_group_array(cls, process_identifier: str) -> list[ProcessGroupLite]:
        parent_group_lites_with_cache = cls.get_parent_group_array_and_cache_it(process_identifier, {})
        return parent_group_lites_with_cache["process_groups"]

    @classmethod
    def get_process_groups(cls, process_group_id: str | None = None) -> list[ProcessGroup]:
        """Returns the process_groups."""
        process_groups = cls.__scan_process_groups(process_group_id)
        process_groups.sort()
        return process_groups

    @classmethod
    def get_process_groups_for_api(
        cls,
        process_group_id: str | None = None,
        user: UserModel | None = None,
    ) -> list[ProcessGroup]:
        process_groups = cls.get_process_groups(process_group_id)

        permission_to_check = "read"
        permission_base_uri = "/process-groups"

        if user is None:
            user = UserService.current_user()

        # if user has access to uri/* with that permission then there's no reason to check each one individually
        guid_of_non_existent_item_to_check_perms_against = str(uuid.uuid4())
        has_permission = AuthorizationService.user_has_permission(
            user=user,
            permission=permission_to_check,
            target_uri=f"{permission_base_uri}/{guid_of_non_existent_item_to_check_perms_against}",
        )
        if has_permission:
            return process_groups

        permission_assignments = AuthorizationService.all_permission_assignments_for_user(user=user)

        new_process_group_list = []
        denied_parent_ids: set[str] = set()
        for process_group in process_groups:
            modified_process_group_id = ProcessModelInfo.modify_process_identifier_for_path_param(process_group.id)
            target_uri = f"{permission_base_uri}/{modified_process_group_id}"
            has_permission = AuthorizationService.permission_assignments_include(
                permission_assignments=permission_assignments,
                permission=permission_to_check,
                target_uri=target_uri,
            )
            if not has_permission:
                for pa in permission_assignments:
                    if (
                        pa.permission == permission_to_check
                        and pa.grant_type == PermitDeny.deny.value
                        and AuthorizationService.target_uri_matches_actual_uri(pa.permission_target.uri, target_uri)
                    ):
                        denied_parent_ids.add(f"{process_group.id}")
                    elif (
                        pa.permission == permission_to_check
                        and pa.grant_type == PermitDeny.permit.value
                        and (
                            pa.permission_target.uri.startswith(f"{target_uri}:")
                            or pa.permission_target.uri.startswith(f"/process-models/{modified_process_group_id}:")
                        )
                    ):
                        has_permission = True
            if has_permission:
                new_process_group_list.append(process_group)

        # remove any process group that also matched a deny permission
        permitted_process_groups = []
        for process_group in new_process_group_list:
            has_denied_permission = False
            for dpi in denied_parent_ids:
                if process_group.id.startswith(f"{dpi}:") or process_group.id == dpi:
                    has_denied_permission = True
            if not has_denied_permission:
                permitted_process_groups.append(process_group)

        return permitted_process_groups

    @classmethod
    def get_process_group(
        cls,
        process_group_id: str,
        find_direct_nested_items: bool = True,
        find_all_nested_items: bool = True,
        create_if_not_exists: bool = False,
    ) -> ProcessGroup:
        """Look for a given process_group, and return it."""
        if os.path.exists(FileSystemService.root_path()):
            process_group_path = FileSystemService.full_path_from_id(process_group_id)
            if cls.is_process_group(process_group_path) or create_if_not_exists:
                return cls.find_or_create_process_group(
                    process_group_path,
                    find_direct_nested_items=find_direct_nested_items,
                    find_all_nested_items=find_all_nested_items,
                )

        raise ProcessEntityNotFoundError("process_group_not_found", f"Process Group Id: {process_group_id}")

    @classmethod
    def add_process_group(cls, process_group: ProcessGroup) -> ProcessGroup:
        return cls.update_process_group(process_group)

    @classmethod
    def update_process_group(cls, process_group: ProcessGroup) -> ProcessGroup:
        cat_path = cls.full_path_from_id(process_group.id)
        os.makedirs(cat_path, exist_ok=True)
        json_path = os.path.join(cat_path, cls.PROCESS_GROUP_JSON_FILE)
        serialized_process_group = process_group.serialized()
        for key in list(serialized_process_group.keys()):
            if key not in PROCESS_GROUP_SUPPORTED_KEYS_FOR_DISK_SERIALIZATION:
                del serialized_process_group[key]
        cls.write_json_file(json_path, serialized_process_group)
        return process_group

    @classmethod
    def process_group_move(cls, original_process_group_id: str, new_location: str) -> ProcessGroup:
        original_group_path = cls.full_path_from_id(original_process_group_id)
        _, original_group_id = os.path.split(original_group_path)
        new_root = os.path.join(FileSystemService.root_path(), new_location)
        new_group_path = os.path.abspath(os.path.join(FileSystemService.root_path(), new_root, original_group_id))
        destination = shutil.move(original_group_path, new_group_path)
        new_process_group = cls.get_process_group(destination)
        return new_process_group

    @classmethod
    def __get_all_nested_models(cls, group_path: str) -> list:
        all_nested_models = []
        for _root, dirs, _files in os.walk(group_path):
            for dir in dirs:
                model_dir = os.path.join(group_path, dir)
                if ProcessModelService.is_process_model(model_dir):
                    process_model = cls.get_process_model(model_dir)
                    all_nested_models.append(process_model)
        return all_nested_models

    @classmethod
    def process_group_delete(cls, process_group_id: str) -> None:
        problem_models = []
        path = cls.full_path_from_id(process_group_id)
        if os.path.exists(path):
            nested_models = cls.__get_all_nested_models(path)
            for process_model in nested_models:
                instances = ProcessInstanceModel.query.filter(
                    ProcessInstanceModel.process_model_identifier == process_model.id
                ).all()
                if len(instances) > 0:
                    problem_models.append(process_model)
            if len(problem_models) > 0:
                raise ProcessModelWithInstancesNotDeletableError(
                    f"We cannot delete the group `{process_group_id}`, there are"
                    " models with existing instances inside the group."
                    f" {problem_models}"
                )
            shutil.rmtree(path)

    @classmethod
    def __scan_process_groups(cls, process_group_id: str | None = None) -> list[ProcessGroup]:
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
                if item.is_dir() and cls.is_process_group(item):  # type: ignore
                    scanned_process_group = cls.find_or_create_process_group(item.path)
                    process_groups.append(scanned_process_group)
            return process_groups

    @classmethod
    def restrict_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        allowed_keys = ProcessGroup.get_valid_properties()
        return {key: data[key] for key in data if key in allowed_keys}

    # NOTE: find_all_nested_items was added to avoid potential backwards compatibility issues.
    # we may be able to remove it and always pass "find_direct_nested_items=False" whenever looking
    # through the subdirs of a process group instead.
    @classmethod
    def find_or_create_process_group(
        cls, dir_path: str, find_direct_nested_items: bool = True, find_all_nested_items: bool = True
    ) -> ProcessGroup:
        """Reads the process_group.json file, and any nested directories."""
        cat_path = os.path.join(dir_path, cls.PROCESS_GROUP_JSON_FILE)
        if os.path.exists(cat_path):
            with open(cat_path) as cat_json:
                data = json.load(cat_json)
                # we don't store `id` in the json files, so we add it back in here
                relative_path = os.path.relpath(dir_path, FileSystemService.root_path())
                data["id"] = cls.path_to_id(relative_path)
                restricted_data = cls.restrict_dict(data)
                process_group = ProcessGroup(**restricted_data)
                if process_group is None:
                    raise ApiError(
                        error_code="process_group_could_not_be_loaded_from_disk",
                        message=f"We could not load the process_group from disk from: {dir_path}",
                    )
        else:
            process_group_id = cls.path_to_id(dir_path.replace(FileSystemService.root_path(), ""))
            process_group = ProcessGroup(
                id="",
                display_name=process_group_id,
            )
            cls.write_json_file(cat_path, cls.GROUP_SCHEMA.dump(process_group))
            # we don't store `id` in the json files, so we add it in here
            process_group.id = process_group_id

        process_group.process_models = []
        process_group.process_groups = []

        if find_direct_nested_items is False:
            return process_group

        if find_all_nested_items:
            with os.scandir(dir_path) as nested_items:
                for nested_item in nested_items:
                    if nested_item.is_dir():
                        # TODO: check whether this is a group or model
                        if cls.is_process_group(nested_item.path):
                            # This is a nested group
                            process_group.process_groups.append(
                                cls.find_or_create_process_group(nested_item.path, find_all_nested_items=find_all_nested_items)
                            )
                        elif ProcessModelService.is_process_model(nested_item.path):
                            process_group.process_models.append(
                                cls.__scan_process_model(
                                    nested_item.path,
                                    nested_item.name,
                                )
                            )
                process_group.process_models.sort()
                process_group.process_groups.sort()
        return process_group

    # path might have backslashes on windows, not sure
    # not sure if os.path.join converts forward slashes in the relative_path argument to backslashes:
    #   path = os.path.join(FileSystemService.root_path(), relative_path)
    @classmethod
    def __scan_process_model(
        cls,
        path: str,
        name: str | None = None,
    ) -> ProcessModelInfo:
        json_file_path = os.path.join(path, cls.PROCESS_MODEL_JSON_FILE)

        if os.path.exists(json_file_path):
            with open(json_file_path) as wf_json:
                try:
                    data = json.load(wf_json)
                except JSONDecodeError as jde:
                    raise ApiError(
                        error_code="process_model_json_file_corrupted",
                        message=f"The process_model json file {json_file_path} is corrupted.",
                    ) from jde
                if "process_group_id" in data:
                    data.pop("process_group_id")
                # we don't save `id` in the json file, so we add it back in here.
                relative_path = os.path.relpath(path, FileSystemService.root_path())
                data["id"] = cls.path_to_id(relative_path)
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
                    message=f"Missing name of process model. Path not found: {json_file_path}",
                )

            process_model_info = ProcessModelInfo(
                id="",
                display_name=name,
                description="",
            )
            cls.write_json_file(json_file_path, cls.PROCESS_MODEL_SCHEMA.dump(process_model_info))
            # we don't store `id` in the json files, so we add it in here
            process_model_info.id = name
        return process_model_info
