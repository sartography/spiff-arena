from __future__ import annotations

import os
import shutil
from datetime import datetime
from typing import TYPE_CHECKING

from lxml import etree  # type: ignore
from SpiffWorkflow.bpmn.parser.BpmnParser import BpmnValidator  # type: ignore

from spiffworkflow_backend.exceptions.error import NotAuthorizedError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.file import File
from spiffworkflow_backend.models.file import FileType
from spiffworkflow_backend.models.file import Reference
from spiffworkflow_backend.models.message_triggerable_process_model import MessageTriggerableProcessModel
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.custom_parser import MyCustomParser
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_caller_service import ProcessCallerService
from spiffworkflow_backend.services.process_model_service import ProcessModelService

if TYPE_CHECKING:
    from spiffworkflow_backend.models.process_model import ProcessModelInfo


class ProcessModelFileInvalidError(Exception):
    pass


class SpecFileService(FileSystemService):
    """We store spec files on the file system. This allows us to take advantage of Git for
    syncing and versioning.
     The files are stored in a directory whose path is determined by the category and spec names.
    """

    @staticmethod
    def reference_map(references: list[Reference]) -> dict[str, Reference]:
        """Creates a dict with provided references organized by id."""
        ref_map = {}
        for ref in references:
            ref_map[ref.identifier] = ref
        return ref_map

    @staticmethod
    def get_references_for_process(
        process_model_info: ProcessModelInfo,
    ) -> list[Reference]:
        files = FileSystemService.get_files(process_model_info)
        references = []
        for file in files:
            references.extend(SpecFileService.get_references_for_file(file, process_model_info))
        return references

    @classmethod
    def get_references_for_file(cls, file: File, process_model_info: ProcessModelInfo) -> list[Reference]:
        full_file_path = cls.full_file_path(process_model_info, file.name)
        with open(full_file_path, "rb") as f:
            file_contents = f.read()
        return cls.get_references_for_file_contents(process_model_info, file.name, file_contents)

    # This is designed to isolate xml parsing, which is a security issue, and make it as safe as possible.
    # S320 indicates that xml parsing with lxml is unsafe. To mitigate this, we add options to the parser
    # to make it as safe as we can. No exploits have been demonstrated with this parser, but we will try to stay alert.
    @classmethod
    def get_etree_from_xml_bytes(cls, binary_data: bytes) -> etree.Element:
        etree_xml_parser = etree.XMLParser(resolve_entities=False, remove_comments=True, no_network=True)
        return etree.fromstring(binary_data, parser=etree_xml_parser)  # noqa: S320

    @classmethod
    def get_bpmn_process_ids_for_file_contents(cls, binary_data: bytes) -> list[str]:
        parser = MyCustomParser()
        parser.add_bpmn_xml(cls.get_etree_from_xml_bytes(binary_data))
        return list(parser.process_parsers.keys())

    @classmethod
    def get_references_for_file_contents(
        cls, process_model_info: ProcessModelInfo, file_name: str, binary_data: bytes
    ) -> list[Reference]:
        """Uses spiffworkflow to parse BPMN and DMN files to determine how they can be externally referenced.

        Returns a list of Reference objects that contain the type of reference, the id, the name.
        Ex.
        id = {str} 'Level3'
        name = {str} 'Level 3'
        type = {str} 'process' / 'decision'
        """
        references: list[Reference] = []
        os.path.join(process_model_info.id_for_file_path(), file_name)
        file_type = FileSystemService.file_type(file_name)
        parser = MyCustomParser()
        parser_type = None
        sub_parser = None
        has_lanes = False
        is_executable = True
        is_primary = False
        messages = {}
        correlations = {}
        start_messages = []
        called_element_ids = []
        if file_type.value == FileType.bpmn.value:
            parser.add_bpmn_xml(cls.get_etree_from_xml_bytes(binary_data))
            parser_type = "process"
            sub_parsers = list(parser.process_parsers.values())
            messages = parser.messages
            correlations = parser.correlations
            # to check permissions for call activities
            parser.get_process_dependencies()
        elif file_type.value == FileType.dmn.value:
            parser.add_dmn_xml(cls.get_etree_from_xml_bytes(binary_data))
            sub_parsers = list(parser.dmn_parsers.values())
            parser_type = "decision"
        else:
            return references
        for sub_parser in sub_parsers:
            if parser_type == "process":
                has_lanes = sub_parser.has_lanes()
                is_executable = sub_parser.process_executable
                start_messages = sub_parser.start_messages()
                is_primary = sub_parser.bpmn_id == process_model_info.primary_process_id
                called_element_ids = sub_parser.called_element_ids()

            references.append(
                Reference(
                    identifier=sub_parser.bpmn_id,
                    display_name=sub_parser.get_name(),
                    relative_location=process_model_info.id,
                    type=parser_type,
                    file_name=file_name,
                    messages=messages,
                    correlations=correlations,
                    start_messages=start_messages,
                    called_element_ids=called_element_ids,
                    properties={"is_primary": is_primary, "has_lanes": has_lanes, "is_executable": is_executable},
                )
            )
        return references

    @classmethod
    def validate_bpmn_xml(cls, file_name: str, binary_data: bytes) -> None:
        file_type = FileSystemService.file_type(file_name)
        if file_type.value == FileType.bpmn.value:
            BpmnValidator()
            parser = MyCustomParser()
            try:
                parser.add_bpmn_xml(cls.get_etree_from_xml_bytes(binary_data), filename=file_name)
            except Exception as exception:
                raise ProcessModelFileInvalidError(f"Received error trying to parse bpmn xml: {str(exception)}") from exception

    @classmethod
    def update_file(
        cls,
        process_model_info: ProcessModelInfo,
        file_name: str,
        binary_data: bytes,
        user: UserModel | None = None,
        update_process_cache_only: bool = False,
    ) -> tuple[File, list[Reference]]:
        SpecFileService.assert_valid_file_name(file_name)
        cls.validate_bpmn_xml(file_name, binary_data)

        references = cls.get_references_for_file_contents(process_model_info, file_name, binary_data)
        primary_process_ref = next(
            (ref for ref in references if ref.prop_is_true("is_primary") and ref.prop_is_true("is_executable")), None
        )

        cls.clear_caches_for_item(file_name=file_name, process_model_info=process_model_info)
        all_called_element_ids: set[str] = set()
        for ref in references:
            # If no valid primary process is defined, default to the first process in the
            # updated file.
            if not primary_process_ref and ref.type == "process" and ref.prop_is_true("is_executable"):
                ref.set_prop("is_primary", True)

            if ref.prop_is_true("is_primary"):
                update_hash = {}
                if not process_model_info.primary_file_name:
                    update_hash["primary_process_id"] = ref.identifier
                    update_hash["primary_file_name"] = file_name
                elif file_name == process_model_info.primary_file_name:
                    update_hash["primary_process_id"] = ref.identifier

                if len(update_hash) > 0:
                    ProcessModelService.update_process_model(
                        process_model_info,
                        update_hash,
                    )

            all_called_element_ids = all_called_element_ids | set(ref.called_element_ids)
            if update_process_cache_only:
                cls.update_process_cache(ref)
            else:
                cls.update_all_caches(ref)

        if user is not None:
            called_element_refs = (
                ReferenceCacheModel.basic_query()
                .filter(ReferenceCacheModel.identifier.in_(all_called_element_ids))  # type: ignore
                .all()
            )
            if len(called_element_refs) > 0:
                process_model_identifiers: list[str] = [r.relative_location for r in called_element_refs]
                permitted_process_model_identifiers = ProcessModelService.process_model_identifiers_with_permission_for_user(
                    user=user,
                    permission_to_check="create",
                    permission_base_uri="/v1.0/process-instances",
                    process_model_identifiers=process_model_identifiers,
                )
                unpermitted_process_model_identifiers = set(process_model_identifiers) - set(permitted_process_model_identifiers)
                if len(unpermitted_process_model_identifiers):
                    raise NotAuthorizedError(
                        "You are not authorized to use one or more processes as a called element:"
                        f" {','.join(unpermitted_process_model_identifiers)}"
                    )

        db.session.commit()

        # make sure we save the file as the last thing we do to ensure validations have run
        full_file_path = cls.full_file_path(process_model_info, file_name)
        cls.write_file_data_to_system(full_file_path, binary_data)
        return (cls.to_file_object(file_name, full_file_path), references)

    @classmethod
    def last_modified(cls, process_model: ProcessModelInfo, file_name: str) -> datetime:
        full_file_path = cls.full_file_path(process_model, file_name)
        return FileSystemService._last_modified(full_file_path)

    @classmethod
    def timestamp(cls, process_model: ProcessModelInfo, file_name: str) -> float:
        full_file_path = cls.full_file_path(process_model, file_name)
        return FileSystemService._timestamp(full_file_path)

    @classmethod
    def delete_file(cls, process_model: ProcessModelInfo, file_name: str) -> None:
        cls.clear_caches_for_item(file_name=file_name, process_model_info=process_model)
        full_file_path = cls.full_file_path(process_model, file_name)
        os.remove(full_file_path)

    @staticmethod
    def delete_all_files(process_model: ProcessModelInfo) -> None:
        dir_path = SpecFileService.process_model_full_path(process_model)
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)

    # fixme: Place all the caching stuff in a different service.

    @staticmethod
    def update_all_caches(ref: Reference) -> None:
        SpecFileService.update_process_cache(ref)
        SpecFileService.update_caches_except_process(ref)

    @staticmethod
    def update_caches_except_process(ref: Reference) -> None:
        SpecFileService.update_process_caller_cache(ref)
        SpecFileService.update_message_trigger_cache(ref)

    @staticmethod
    def clear_caches_for_item(
        file_name: str | None = None, process_model_info: ProcessModelInfo | None = None, process_group_id: str | None = None
    ) -> None:
        reference_cache_query = ReferenceCacheModel.basic_query()

        if process_group_id is not None:
            reference_cache_query = reference_cache_query.filter(
                ReferenceCacheModel.relative_location.like(f"{process_group_id}/%")  # type: ignore
            )
        if file_name is not None:
            reference_cache_query = reference_cache_query.filter(ReferenceCacheModel.file_name == file_name)
        if process_model_info is not None:
            reference_cache_query = reference_cache_query.filter(ReferenceCacheModel.relative_location == process_model_info.id)

        records = reference_cache_query.all()
        reference_cache_ids = []
        for record in records:
            reference_cache_ids.append(record.id)

        ProcessCallerService.clear_cache_for_process_ids(reference_cache_ids)

        for record in records:
            db.session.delete(record)

    @staticmethod
    def update_process_cache(ref: Reference) -> None:
        process_id_lookup = ReferenceCacheModel.basic_query().filter_by(identifier=ref.identifier, type=ref.type).first()
        if process_id_lookup is None:
            process_id_lookup = ReferenceCacheModel.from_spec_reference(ref, use_current_cache_generation=True)
            db.session.add(process_id_lookup)
        else:
            if ref.relative_path() != process_id_lookup.relative_path():
                full_bpmn_file_path = SpecFileService.full_path_from_relative_path(process_id_lookup.relative_path())
                # if the old relative bpmn file no longer exists, then assume things were moved around
                # on the file system. Otherwise, assume it is a duplicate process id and error.
                if os.path.isfile(full_bpmn_file_path):
                    raise ProcessModelFileInvalidError(
                        f"Process id ({ref.identifier}) has already been used for "
                        f"{process_id_lookup.relative_path()}. It cannot be reused."
                    )
                else:
                    process_id_lookup.relative_location = ref.relative_location
                    process_id_lookup.file_name = ref.file_name
                    db.session.add(process_id_lookup)

    @staticmethod
    def update_process_caller_cache(ref: Reference) -> None:
        ProcessCallerService.add_caller(ref.identifier, ref.called_element_ids)

    @staticmethod
    def update_message_trigger_cache(ref: Reference) -> None:
        """Assure we know which messages can trigger the start of a process."""
        current_triggerable_processes = MessageTriggerableProcessModel.query.filter_by(
            file_name=ref.file_name, process_model_identifier=ref.relative_location
        ).all()
        for message_name in ref.start_messages:
            message_triggerable_process_model = MessageTriggerableProcessModel.query.filter_by(
                message_name=message_name,
            ).first()
            if message_triggerable_process_model is None:
                message_triggerable_process_model = MessageTriggerableProcessModel(
                    message_name=message_name,
                    process_model_identifier=ref.relative_location,
                    file_name=ref.file_name,
                )
                db.session.add(message_triggerable_process_model)
            else:
                existing_model_identifier = message_triggerable_process_model.process_model_identifier
                if existing_model_identifier != ref.relative_location:
                    raise ProcessModelFileInvalidError(
                        f"Message model is already used to start process model {existing_model_identifier}"
                    )
                elif message_triggerable_process_model.file_name is None:
                    message_triggerable_process_model.file_name = ref.file_name
                    db.session.add(message_triggerable_process_model)
                current_triggerable_processes.remove(message_triggerable_process_model)
        for trigger_pm in current_triggerable_processes:
            db.session.delete(trigger_pm)
