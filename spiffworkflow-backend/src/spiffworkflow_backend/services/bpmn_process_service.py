import copy
import json
import time
from hashlib import sha256

from flask import current_app
from SpiffWorkflow.bpmn.serializer.default.task_spec import EventConverter  # type: ignore
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer  # type: ignore
from SpiffWorkflow.bpmn.specs.bpmn_process_spec import BpmnProcessSpec  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.spiff.serializer.config import SPIFF_CONFIG  # type: ignore
from SpiffWorkflow.spiff.serializer.task_spec import ServiceTaskConverter  # type: ignore
from SpiffWorkflow.spiff.serializer.task_spec import StandardLoopTaskConverter
from SpiffWorkflow.spiff.specs.defaults import ServiceTask  # type: ignore
from SpiffWorkflow.spiff.specs.defaults import StandardLoopTask
from sqlalchemy import and_

from spiffworkflow_backend.constants import SPIFFWORKFLOW_BACKEND_SERIALIZER_VERSION
from spiffworkflow_backend.data_stores.json import JSONDataStore
from spiffworkflow_backend.data_stores.json import JSONDataStoreConverter
from spiffworkflow_backend.data_stores.json import JSONFileDataStore
from spiffworkflow_backend.data_stores.json import JSONFileDataStoreConverter
from spiffworkflow_backend.data_stores.kkv import KKVDataStore
from spiffworkflow_backend.data_stores.kkv import KKVDataStoreConverter
from spiffworkflow_backend.data_stores.typeahead import TypeaheadDataStore
from spiffworkflow_backend.data_stores.typeahead import TypeaheadDataStoreConverter
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.bpmn_process_definition_relationship import BpmnProcessDefinitionRelationshipModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel
from spiffworkflow_backend.services.custom_service_task import CustomServiceTask
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.workflow_spec_service import IdToBpmnProcessSpecMapping
from spiffworkflow_backend.services.workflow_spec_service import WorkflowSpecService
from spiffworkflow_backend.specs.start_event import StartEvent


# this custom converter is just so we use 'ServiceTask' as the typename in the serialization
# rather than 'CustomServiceTask'
class CustomServiceTaskConverter(ServiceTaskConverter):  # type: ignore
    def __init__(self, target_class, registry, typename: str = "ServiceTask"):  # type: ignore
        super().__init__(target_class, registry, typename)


SPIFF_CONFIG[StandardLoopTask] = StandardLoopTaskConverter
SPIFF_CONFIG[CustomServiceTask] = CustomServiceTaskConverter
del SPIFF_CONFIG[ServiceTask]

SPIFF_CONFIG[StartEvent] = EventConverter
SPIFF_CONFIG[JSONDataStore] = JSONDataStoreConverter
SPIFF_CONFIG[JSONFileDataStore] = JSONFileDataStoreConverter
SPIFF_CONFIG[KKVDataStore] = KKVDataStoreConverter
SPIFF_CONFIG[TypeaheadDataStore] = TypeaheadDataStoreConverter

# Notes on bpmn_definition_to_task_definitions_mappings:
#
# this caches the bpmn_process_definition_identifier and task_identifier back to the bpmn_process_id
# intthe database. This is to cut down on database queries while adding new tasks to the database.
# Structure:
#   { "[[BPMN_PROCESS_DEFINITION_IDENTIFIER]]": {
#       "[[TASK_IDENTIFIER]]": [[TASK_DEFINITION]],
#       "bpmn_process_definition": [[BPMN_PROCESS_DEFINITION]] }
#   }
# To use from a spiff_task:
#   [spiff_task.workflow.spec.name][spiff_task.task_spec.name]


class BpmnProcessService:
    wf_spec_converter = BpmnWorkflowSerializer.configure(SPIFF_CONFIG)
    serializer = BpmnWorkflowSerializer(wf_spec_converter, version=SPIFFWORKFLOW_BACKEND_SERIALIZER_VERSION)

    @classmethod
    def persist_bpmn_process_definition(
        cls, process_model_identifier: str, bpmn_definition_to_task_definitions_mappings: dict | None = None
    ) -> BpmnProcessDefinitionModel:
        if bpmn_definition_to_task_definitions_mappings is None:
            bpmn_definition_to_task_definitions_mappings = {}

        (
            bpmn_process_spec,
            subprocesses,
        ) = cls.get_process_model_and_subprocesses(process_model_identifier)

        bpmn_process_instance = cls.get_bpmn_process_instance_from_workflow_spec(bpmn_process_spec, subprocesses)

        bpmn_process_definition_parent = cls.add_bpmn_process_definitions(
            cls.serialize(bpmn_process_instance),
            bpmn_definition_to_task_definitions_mappings=bpmn_definition_to_task_definitions_mappings,
        )

        cls.save_to_database(
            bpmn_definition_to_task_definitions_mappings, bpmn_process_definition_parent=bpmn_process_definition_parent
        )
        return bpmn_process_definition_parent

    @classmethod
    def add_bpmn_process_definitions(
        cls,
        bpmn_process_dict: dict,
        bpmn_definition_to_task_definitions_mappings: dict,
    ) -> BpmnProcessDefinitionModel:
        """Adds serialized_bpmn_definition records to the db session.

        Expects the calling method to commit it.
        """

        bpmn_dict_keys = BpmnProcessDefinitionModel.keys_for_full_process_model_hash()
        bpmn_spec_dict = {}
        for bpmn_key, bpmn_value in bpmn_process_dict.items():
            if bpmn_key in bpmn_dict_keys:
                bpmn_spec_dict[bpmn_key] = bpmn_value

        # store only if mappings is currently empty. this also would mean this is a new instance that has never saved before
        store_bpmn_definition_mappings = not bpmn_definition_to_task_definitions_mappings
        bpmn_process_definition_parent = cls._store_bpmn_process_definition(
            bpmn_spec_dict["spec"],
            bpmn_definition_to_task_definitions_mappings=bpmn_definition_to_task_definitions_mappings,
            store_bpmn_definition_mappings=store_bpmn_definition_mappings,
            full_bpmn_spec_dict=bpmn_spec_dict,
        )
        for process_bpmn_properties in bpmn_spec_dict["subprocess_specs"].values():
            cls._store_bpmn_process_definition(
                process_bpmn_properties,
                bpmn_definition_to_task_definitions_mappings=bpmn_definition_to_task_definitions_mappings,
                store_bpmn_definition_mappings=store_bpmn_definition_mappings,
            )
        return bpmn_process_definition_parent

    @classmethod
    def get_definition_dict_for_bpmn_process_definition(
        cls,
        bpmn_process_definition: BpmnProcessDefinitionModel,
        bpmn_definition_to_task_definitions_mappings: dict,
    ) -> dict:
        cls._update_bpmn_definition_mappings(
            bpmn_definition_to_task_definitions_mappings,
            bpmn_process_definition.bpmn_identifier,
            bpmn_process_definition=bpmn_process_definition,
        )
        task_definitions = TaskDefinitionModel.query.filter_by(bpmn_process_definition_id=bpmn_process_definition.id).all()
        bpmn_process_definition_dict: dict = copy.deepcopy(bpmn_process_definition.properties_json)
        bpmn_process_definition_dict["task_specs"] = {}
        for task_definition in task_definitions:
            bpmn_process_definition_dict["task_specs"][task_definition.bpmn_identifier] = task_definition.properties_json
            cls._update_bpmn_definition_mappings(
                bpmn_definition_to_task_definitions_mappings,
                bpmn_process_definition.bpmn_identifier,
                task_definition=task_definition,
            )
        return bpmn_process_definition_dict

    @classmethod
    def set_definition_dict_for_bpmn_subprocess_definitions(
        cls,
        bpmn_process_definition: BpmnProcessDefinitionModel,
        spiff_bpmn_process_dict: dict,
        bpmn_definition_to_task_definitions_mappings: dict,
    ) -> None:
        # find all child subprocesses of a process
        bpmn_process_subprocess_definitions = (
            BpmnProcessDefinitionModel.query.join(
                BpmnProcessDefinitionRelationshipModel,
                BpmnProcessDefinitionModel.id == BpmnProcessDefinitionRelationshipModel.bpmn_process_definition_child_id,
            )
            .filter_by(bpmn_process_definition_parent_id=bpmn_process_definition.id)
            .all()
        )

        bpmn_subprocess_definition_bpmn_identifiers = {}
        for bpmn_subprocess_definition in bpmn_process_subprocess_definitions:
            cls._update_bpmn_definition_mappings(
                bpmn_definition_to_task_definitions_mappings,
                bpmn_subprocess_definition.bpmn_identifier,
                bpmn_process_definition=bpmn_subprocess_definition,
            )
            bpmn_process_definition_dict: dict = bpmn_subprocess_definition.properties_json
            spiff_bpmn_process_dict["subprocess_specs"][bpmn_subprocess_definition.bpmn_identifier] = bpmn_process_definition_dict
            spiff_bpmn_process_dict["subprocess_specs"][bpmn_subprocess_definition.bpmn_identifier]["task_specs"] = {}
            bpmn_subprocess_definition_bpmn_identifiers[bpmn_subprocess_definition.id] = (
                bpmn_subprocess_definition.bpmn_identifier
            )

        task_definitions = TaskDefinitionModel.query.filter(
            TaskDefinitionModel.bpmn_process_definition_id.in_(bpmn_subprocess_definition_bpmn_identifiers.keys())  # type: ignore
        ).all()
        for task_definition in task_definitions:
            bpmn_subprocess_definition_bpmn_identifier = bpmn_subprocess_definition_bpmn_identifiers[
                task_definition.bpmn_process_definition_id
            ]
            cls._update_bpmn_definition_mappings(
                bpmn_definition_to_task_definitions_mappings,
                bpmn_subprocess_definition_bpmn_identifier,
                task_definition=task_definition,
            )
            spiff_bpmn_process_dict["subprocess_specs"][bpmn_subprocess_definition_bpmn_identifier]["task_specs"][
                task_definition.bpmn_identifier
            ] = task_definition.properties_json

    @classmethod
    def truncate_string(cls, input_string: str | None, max_length: int) -> str | None:
        if input_string is None:
            return None
        return input_string[:max_length]

    @classmethod
    def get_process_model_and_subprocesses(
        cls,
        process_model_identifier: str,
        process_id_to_run: str | None = None,
    ) -> tuple[BpmnProcessSpec, IdToBpmnProcessSpecMapping]:
        process_model_info = ProcessModelService.get_process_model(process_model_identifier)
        if process_model_info is None:
            raise (
                ApiError(
                    "process_model_not_found",
                    f"The given process model was not found: {process_model_identifier}.",
                )
            )
        spec_files = FileSystemService.get_files(process_model_info)
        return WorkflowSpecService.get_spec(spec_files, process_model_info, process_id_to_run=process_id_to_run)

    @staticmethod
    def get_bpmn_process_instance_from_workflow_spec(
        spec: BpmnProcessSpec,
        subprocesses: IdToBpmnProcessSpecMapping | None = None,
    ) -> BpmnWorkflow:
        bpmn_process_instance = BpmnWorkflow(
            spec,
            subprocess_specs=subprocesses,
        )
        return bpmn_process_instance

    @classmethod
    def serialize(cls, bpmn_process_instance: BpmnWorkflow) -> dict:
        return cls.serializer.to_dict(bpmn_process_instance)  # type: ignore

    @classmethod
    def save_to_database(
        cls,
        bpmn_definition_to_task_definitions_mappings: dict,
        bpmn_process_definition_parent: BpmnProcessDefinitionModel | None = None,
    ) -> None:
        try:
            parent_id = None
            subprocess_ids = []
            for _bpmn_process_identifier, entity in bpmn_definition_to_task_definitions_mappings.items():
                bpmn_process_definition = entity["bpmn_process_definition"]
                bpd_id = 0
                if bpmn_process_definition.id is None:
                    bpmn_process_definition_dict = {
                        "single_process_hash": bpmn_process_definition.single_process_hash,
                        "full_process_model_hash": bpmn_process_definition.full_process_model_hash,
                        "bpmn_identifier": bpmn_process_definition.bpmn_identifier,
                        "bpmn_name": bpmn_process_definition.bpmn_name,
                        "properties_json": bpmn_process_definition.properties_json,
                        "updated_at_in_seconds": round(time.time()),
                        "created_at_in_seconds": round(time.time()),
                    }
                    result = BpmnProcessDefinitionModel.insert_or_update_record(bpmn_process_definition_dict)
                    if result and result.inserted_primary_key is not None:
                        bpd_id = result.inserted_primary_key[0]
                if bpd_id == 0:
                    bpdm = BpmnProcessDefinitionModel.query.filter(
                        and_(
                            BpmnProcessDefinitionModel.full_process_model_hash == bpmn_process_definition.full_process_model_hash,
                            BpmnProcessDefinitionModel.single_process_hash == bpmn_process_definition.single_process_hash,
                        )
                    ).first()
                    if bpdm is None:
                        raise RuntimeError(
                            "Failed to look up BpmnProcessDefinitionModel after insert_or_update_record "
                            f"for full_process_model_hash={bpmn_process_definition.full_process_model_hash!r} "
                            f"and single_process_hash={bpmn_process_definition.single_process_hash!r}."
                        )
                    bpd_id = bpdm.id

                if bpmn_process_definition_parent is not None:
                    if bpmn_process_definition_parent.bpmn_identifier == _bpmn_process_identifier:
                        parent_id = bpd_id
                    else:
                        subprocess_ids.append(bpd_id)

                for identifier, definition in entity.items():
                    if definition.id is None and identifier != "bpmn_process_definition":
                        task_definition_dict = {
                            "bpmn_process_definition_id": bpd_id,
                            "bpmn_identifier": definition.bpmn_identifier,
                            "bpmn_name": definition.bpmn_name,
                            "properties_json": definition.properties_json,
                            "typename": definition.typename,
                            "updated_at_in_seconds": round(time.time()),
                            "created_at_in_seconds": round(time.time()),
                        }
                        TaskDefinitionModel.insert_or_update_record(task_definition_dict)

            if parent_id:
                for bpd_id in subprocess_ids:
                    bpmn_process_definition_relationship = BpmnProcessDefinitionRelationshipModel.query.filter_by(
                        bpmn_process_definition_parent_id=parent_id,
                        bpmn_process_definition_child_id=bpd_id,
                    ).first()
                    if bpmn_process_definition_relationship is None:
                        bpmn_process_definition_relationship = BpmnProcessDefinitionRelationshipModel(
                            bpmn_process_definition_parent_id=parent_id,
                            bpmn_process_definition_child_id=bpd_id,
                        )
                        db.session.add(bpmn_process_definition_relationship)

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @classmethod
    def extract_human_task_definitions(cls, bpmn_definition_to_task_definitions_mappings: dict) -> list[TaskDefinitionModel]:
        human_tasks = []
        for _bpmn_process_identifier, entity in bpmn_definition_to_task_definitions_mappings.items():
            for task_identifier, task_definition in entity.items():
                if task_identifier != "bpmn_process_definition" and task_definition.is_human_task():
                    human_tasks.append(task_definition)

        return human_tasks

    @classmethod
    def search_task_definitions(cls, process_model_identifier: str, body: dict | None = None) -> list[dict[str, object]]:
        body = body or {}
        include_dependencies = body.get("include_dependencies", True) is not False
        task_types = set(body.get("task_types") or [])
        extension_names = set(body.get("extension_names") or [])
        extension_names.update(body.get("extension_types") or [])
        extension_name = body.get("extension_name") or body.get("extension_type")
        if extension_name:
            extension_names.add(extension_name)
        extension_property_filters = cls._extension_property_filters_from_body(body)

        process_model_info = ProcessModelService.get_process_model(process_model_identifier)
        if process_model_info is None:
            raise ApiError(
                "process_model_not_found",
                f"The given process model was not found: {process_model_identifier}.",
            )

        bpmn_definition_to_task_definitions_mappings: dict = {}
        cls.persist_bpmn_process_definition(process_model_identifier, bpmn_definition_to_task_definitions_mappings)
        task_location_index = cls._task_location_index_for_process_definitions(
            process_model_info,
            set(bpmn_definition_to_task_definitions_mappings.keys()),
        )

        results = []
        for process_identifier, entity in bpmn_definition_to_task_definitions_mappings.items():
            if not include_dependencies and process_identifier != process_model_info.primary_process_id:
                continue

            bpmn_process_definition = entity.get("bpmn_process_definition")
            spec_reference = cls._spec_reference_for_process(process_identifier, process_model_info)
            for task_identifier, task_definition in entity.items():
                if task_identifier == "bpmn_process_definition":
                    continue
                if task_types and task_definition.typename not in task_types:
                    continue
                extensions = task_definition.properties_json.get("extensions") or {}
                if not isinstance(extensions, dict):
                    extensions = {}
                if not cls._matches_extension_names(extensions, extension_names):
                    continue
                if not cls._matches_extension_property_filters(extensions, extension_property_filters):
                    continue

                extension_properties = extensions.get("properties") or {}
                if not isinstance(extension_properties, dict):
                    extension_properties = {}
                task_location = task_location_index.get(
                    (process_identifier, task_definition.bpmn_identifier),
                    {
                        "process_model_identifier": spec_reference.relative_location,
                        "file_name": spec_reference.file_name,
                    },
                )

                results.append(
                    {
                        "bpmn_identifier": task_definition.bpmn_identifier,
                        "bpmn_name": task_definition.bpmn_name,
                        "typename": task_definition.typename,
                        "bpmn_process_identifier": process_identifier,
                        "bpmn_process_name": getattr(bpmn_process_definition, "bpmn_name", None),
                        "process_model_identifier": task_location["process_model_identifier"],
                        "modified_process_model_identifier": ProcessModelInfo.modify_process_identifier_for_path_param(
                            task_location["process_model_identifier"]
                        ),
                        "file_name": task_location["file_name"],
                        "extensions": extensions,
                        "extension_properties": extension_properties,
                        "properties_json": task_definition.properties_json,
                    }
                )

        return sorted(
            results,
            key=lambda item: (
                str(item.get("process_model_identifier") or ""),
                str(item.get("file_name") or ""),
                str(item.get("bpmn_process_identifier") or ""),
                str(item.get("bpmn_identifier") or ""),
            ),
        )

    @staticmethod
    def _extension_property_filters_from_body(body: dict) -> list[dict]:
        filters = body.get("extension_properties") or []
        if isinstance(filters, dict):
            filters = [filters]
        elif not isinstance(filters, list):
            filters = []

        property_name = body.get("extension_property_name") or body.get("property_name")
        if property_name:
            filters = [*filters, {"name": property_name, "exists": True}]
        return [filter_item for filter_item in filters if isinstance(filter_item, dict)]

    @staticmethod
    def _matches_extension_names(extensions: dict, extension_names: set[str]) -> bool:
        return all(extension_name in extensions for extension_name in extension_names)

    @staticmethod
    def _matches_extension_property_filters(extensions: dict, filters: list[dict]) -> bool:
        if not filters:
            return True

        extension_properties = extensions.get("properties") or {}
        if not isinstance(extension_properties, dict):
            extension_properties = {}

        for filter_item in filters:
            property_name = filter_item.get("name") or filter_item.get("property_name")
            if not property_name:
                continue

            property_exists = property_name in extension_properties
            expected_exists = filter_item.get("exists")
            if expected_exists is True and not property_exists:
                return False
            if expected_exists is False and property_exists:
                return False
            if "value" in filter_item and extension_properties.get(property_name) != filter_item["value"]:
                return False
            if "values" in filter_item and extension_properties.get(property_name) not in filter_item["values"]:
                return False

        return True

    @staticmethod
    def _spec_reference_for_process(process_identifier: str, process_model_info: ProcessModelInfo) -> ReferenceCacheModel:
        spec_reference = ReferenceCacheModel.basic_query().filter_by(identifier=process_identifier, type="process").first()
        if spec_reference is not None:
            return spec_reference

        WorkflowSpecService.backfill_missing_spec_reference_records(process_identifier)
        db.session.flush()
        spec_reference = ReferenceCacheModel.basic_query().filter_by(identifier=process_identifier, type="process").first()
        if spec_reference is not None:
            return spec_reference

        return ReferenceCacheModel(
            identifier=process_identifier,
            display_name=process_identifier,
            relative_location=process_model_info.id,
            type="process",
            file_name=process_model_info.primary_file_name or "",
            properties={},
        )

    @classmethod
    def _task_location_index_for_process_definitions(
        cls,
        process_model_info: ProcessModelInfo,
        process_identifiers: set[str],
    ) -> dict[tuple[str, str], dict[str, str]]:
        process_model_files = {
            (process_model_info.id, file.name)
            for file in FileSystemService.get_files(process_model_info)
            if file.type == "bpmn"
        }
        for process_identifier in process_identifiers:
            spec_reference = cls._spec_reference_for_process(process_identifier, process_model_info)
            if spec_reference.file_name:
                process_model_files.add((spec_reference.relative_location, spec_reference.file_name))

        index: dict[tuple[str, str], dict[str, str]] = {}
        for process_model_identifier, file_name in process_model_files:
            located_process_model = ProcessModelService.get_process_model(process_model_identifier)
            if located_process_model is None:
                continue
            try:
                bpmn_xml = FileSystemService.get_data(located_process_model, file_name)
                bpmn_root = ProcessModelService.get_etree_from_xml_bytes(bpmn_xml)
            except Exception as ex:
                current_app.logger.warning(
                    "Failed to index BPMN task locations for %s/%s: %s",
                    process_model_identifier,
                    file_name,
                    ex,
                )
                continue
            cls._index_bpmn_element_locations(
                bpmn_root,
                process_model_identifier=process_model_identifier,
                file_name=file_name,
                index=index,
            )
        return index

    @classmethod
    def _index_bpmn_element_locations(
        cls,
        element,
        *,
        process_model_identifier: str,
        file_name: str,
        index: dict[tuple[str, str], dict[str, str]],
        scope_identifier: str | None = None,
    ) -> None:
        element_identifier = element.get("id")
        if scope_identifier and element_identifier:
            index.setdefault(
                (scope_identifier, element_identifier),
                {
                    "process_model_identifier": process_model_identifier,
                    "file_name": file_name,
                },
            )

        child_scope_identifier = scope_identifier
        if element_identifier and cls._xml_local_name(element.tag) in {"process", "subProcess"}:
            child_scope_identifier = element_identifier

        for child in element:
            cls._index_bpmn_element_locations(
                child,
                process_model_identifier=process_model_identifier,
                file_name=file_name,
                index=index,
                scope_identifier=child_scope_identifier,
            )

    @staticmethod
    def _xml_local_name(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    @classmethod
    def _store_bpmn_process_definition(
        cls,
        process_bpmn_properties: dict,
        bpmn_definition_to_task_definitions_mappings: dict,
        store_bpmn_definition_mappings: bool = False,
        full_bpmn_spec_dict: dict | None = None,
    ) -> BpmnProcessDefinitionModel:
        process_bpmn_identifier = process_bpmn_properties["name"]
        process_bpmn_name = process_bpmn_properties["description"]

        bpmn_process_definition: BpmnProcessDefinitionModel | None = None
        single_process_hash = sha256(json.dumps(process_bpmn_properties, sort_keys=True).encode("utf8")).hexdigest()
        full_process_model_hash = None
        if full_bpmn_spec_dict is not None:
            full_process_model_hash = sha256(json.dumps(full_bpmn_spec_dict, sort_keys=True).encode("utf8")).hexdigest()
            bpmn_process_definition = BpmnProcessDefinitionModel.query.filter_by(
                full_process_model_hash=full_process_model_hash
            ).first()
        else:
            bpmn_process_definition = BpmnProcessDefinitionModel.query.filter_by(single_process_hash=single_process_hash).first()

        if bpmn_process_definition is None:
            task_specs = process_bpmn_properties.pop("task_specs")
            bpmn_process_definition_dict = {
                "single_process_hash": single_process_hash,
                "full_process_model_hash": full_process_model_hash,
                "bpmn_identifier": process_bpmn_identifier,
                "bpmn_name": process_bpmn_name,
                "properties_json": process_bpmn_properties,
            }
            bpmn_process_definition = BpmnProcessDefinitionModel(**bpmn_process_definition_dict)
            process_bpmn_properties["task_specs"] = task_specs
            cls._update_bpmn_definition_mappings(
                bpmn_definition_to_task_definitions_mappings,
                bpmn_process_definition.bpmn_identifier,
                bpmn_process_definition=bpmn_process_definition,
            )
            for task_bpmn_identifier, task_bpmn_properties in task_specs.items():
                task_bpmn_name = task_bpmn_properties["bpmn_name"]
                truncated_name = cls.truncate_string(task_bpmn_name, 255)
                task_bpmn_properties["bpmn_name"] = truncated_name
                task_definition = TaskDefinitionModel(
                    bpmn_process_definition=bpmn_process_definition,
                    bpmn_identifier=task_bpmn_identifier,
                    bpmn_name=truncated_name,
                    properties_json=task_bpmn_properties,
                    typename=task_bpmn_properties["typename"],
                )
                if store_bpmn_definition_mappings:
                    cls._update_bpmn_definition_mappings(
                        bpmn_definition_to_task_definitions_mappings,
                        process_bpmn_identifier,
                        task_definition=task_definition,
                    )
        elif store_bpmn_definition_mappings:
            # this should only ever happen when new process instances use a pre-existing bpmn process definitions
            # otherwise this should get populated on processor initialization
            cls._update_bpmn_definition_mappings(
                bpmn_definition_to_task_definitions_mappings,
                process_bpmn_identifier,
                bpmn_process_definition=bpmn_process_definition,
            )
            task_definitions = TaskDefinitionModel.query.filter_by(bpmn_process_definition_id=bpmn_process_definition.id).all()
            for task_definition in task_definitions:
                cls._update_bpmn_definition_mappings(
                    bpmn_definition_to_task_definitions_mappings,
                    process_bpmn_identifier,
                    task_definition=task_definition,
                )
        return bpmn_process_definition

    @classmethod
    def _update_bpmn_definition_mappings(
        cls,
        bpmn_definition_to_task_definitions_mappings: dict,
        bpmn_process_definition_identifier: str,
        task_definition: TaskDefinitionModel | None = None,
        bpmn_process_definition: BpmnProcessDefinitionModel | None = None,
    ) -> None:
        if bpmn_process_definition_identifier not in bpmn_definition_to_task_definitions_mappings:
            bpmn_definition_to_task_definitions_mappings[bpmn_process_definition_identifier] = {}

        if task_definition is not None:
            bpmn_definition_to_task_definitions_mappings[bpmn_process_definition_identifier][task_definition.bpmn_identifier] = (
                task_definition
            )

        if bpmn_process_definition is not None:
            bpmn_definition_to_task_definitions_mappings[bpmn_process_definition_identifier]["bpmn_process_definition"] = (
                bpmn_process_definition
            )
