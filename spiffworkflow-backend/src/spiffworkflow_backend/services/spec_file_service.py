"""Spec_file_service."""
import os
import shutil
from datetime import datetime
from typing import Any, Type
from typing import List
from typing import Optional

from SpiffWorkflow.dmn.parser.BpmnDmnParser import BpmnDmnParser
from SpiffWorkflow.bpmn.parser.ProcessParser import ProcessParser
from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db
from lxml import etree  # type: ignore
from lxml.etree import _Element  # type: ignore
from lxml.etree import Element as EtreeElement
from SpiffWorkflow.bpmn.parser.ValidationException import ValidationException  # type: ignore

from spiffworkflow_backend.models.spec_reference import SpecReferenceCache
from spiffworkflow_backend.models.file import File
from spiffworkflow_backend.models.file import SpecReference
from spiffworkflow_backend.models.file import FileType
from spiffworkflow_backend.models.message_correlation_property import (
    MessageCorrelationPropertyModel,
)
from spiffworkflow_backend.models.message_model import MessageModel
from spiffworkflow_backend.models.message_triggerable_process_model import (
    MessageTriggerableProcessModel,
)
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.custom_parser import MyCustomParser
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_model_service import ProcessModelService


class ProcessModelFileNotFoundError(Exception):
    """ProcessModelFileNotFoundError."""


class SpecFileService(FileSystemService):
    """SpecFileService."""

    """We store spec files on the file system. This allows us to take advantage of Git for
       syncing and versioning.
        The files are stored in a directory whose path is determined by the category and spec names.
    """

    @staticmethod
    def get_files(
        process_model_info: ProcessModelInfo,
        file_name: Optional[str] = None,
        extension_filter: str = "",
    ) -> List[File]:
        """Return all files associated with a workflow specification."""
        # path = SpecFileService.workflow_path(process_model_info)
        path = os.path.join(FileSystemService.root_path(), process_model_info.id)
        files = SpecFileService._get_files(path, file_name)
        if extension_filter != "":
            files = list(
                filter(lambda file: file.name.endswith(extension_filter), files)
            )
        return files

    @staticmethod
    def reference_map(references: list[SpecReference]) -> dict[str, SpecReference]:
        """ Creates a dict with provided references organized by id. """
        ref_map = {}
        for ref in references:
            ref_map[ref.identifier] = ref
        return ref_map

    @staticmethod
    def get_references(process_models: List[ProcessModelInfo]) -> list[SpecReference]:
        """Returns all references -- process_ids, and decision ids, across all process models provided"""
        references = []
        for process_model in process_models:
            references.extend(SpecFileService.get_references_for_process(process_model))

    @staticmethod
    def get_references_for_process(process_model_info: ProcessModelInfo) -> list[SpecReference]:
        files = SpecFileService.get_files(process_model_info)
        references = []
        for file in files:
            references.extend(SpecFileService.get_references_for_file(file, process_model_info))
        return references

    @staticmethod
    def get_references_for_file(file: File, process_model_info: ProcessModelInfo) -> list[SpecReference]:
        """Uses spiffworkflow to parse BPMN and DMN files to determine how they can be externally referenced.

        Returns a list of Reference objects that contain the type of reference, the id, the name.
        Ex.
        id = {str} 'Level3'
        name = {str} 'Level 3'
        type = {str} 'process' / 'decision'
        """
        references: list[SpecReference] = []
        full_file_path = SpecFileService.file_path(process_model_info, file.name)
        file_path = os.path.join(process_model_info.id, file.name)
        parser = MyCustomParser()
        parser_type = None
        sub_parser = None
        has_lanes = False
        is_executable = True
        is_primary = False
        messages = {}
        correlations = {}
        start_messages = []
        if file.type == FileType.bpmn.value:
            parser.add_bpmn_file(full_file_path)
            parser_type = "process"
            sub_parsers = list(parser.process_parsers.values())
            messages = parser.messages
            correlations = parser.correlations
        elif file.type == FileType.dmn.value:
            parser.add_dmn_file(full_file_path)
            sub_parsers = list(parser.dmn_parsers.values())
            parser_type = "decision"
        else:
            return references
        for sub_parser in sub_parsers:
            if parser_type == 'process':
                has_lanes = sub_parser.has_lanes()
                executable = sub_parser.process_executable
                start_messages = sub_parser.start_messages()
                is_primary = sub_parser.get_id() == process_model_info.primary_process_id
            references.append(SpecReference(
                    identifier=sub_parser.get_id(), display_name=sub_parser.get_name(),
                    process_model_id=process_model_info.id,
                    type=parser_type,
                    file_name=file.name, relative_path=file_path, has_lanes=has_lanes,
                    is_executable=is_executable, messages=messages, is_primary=is_primary,
                    correlations=correlations, start_messages=start_messages
                ))
        return references

    @staticmethod
    def add_file(
        process_model_info: ProcessModelInfo, file_name: str, binary_data: bytes
    ) -> File:
        """Add_file."""
        # Same as update
        return SpecFileService.update_file(process_model_info, file_name, binary_data)

    @staticmethod
    def update_file(process_model_info: ProcessModelInfo, file_name: str, binary_data: bytes
    ) -> File:
        """Update_file."""
        SpecFileService.assert_valid_file_name(file_name)
        file_path = os.path.join(
            FileSystemService.root_path(), process_model_info.id, file_name
        )
        SpecFileService.write_file_data_to_system(file_path, binary_data)
        file = SpecFileService.to_file_object(file_name, file_path)

        references = SpecFileService.get_references_for_file(file, process_model_info)
        primary_process_ref = next((ref for ref in references if ref.is_primary), None)
        for ref in references:
            # If no valid primary process is defined, default to the first process in the
            # updated file.
            if not primary_process_ref and ref.type == "process":
                ref.is_primary = True

            if ref.is_primary:
                ProcessModelService().update_spec(
                    process_model_info, {
                        "primary_process_id": ref.identifier,
                        "primary_file_name": file_name,
                        "is_review": ref.has_lanes,
                    }
                )
            SpecFileService.update_process_cache(ref)
            SpecFileService.update_message_cache(ref)
            SpecFileService.update_message_trigger_cache(ref, process_model_info)
            SpecFileService.update_correlation_cache(ref)

        return file

    @staticmethod
    def get_data(process_model_info: ProcessModelInfo, file_name: str) -> bytes:
        """Get_data."""
        # file_path = SpecFileService.file_path(process_model_info, file_name)
        file_path = os.path.join(
            FileSystemService.root_path(), process_model_info.id, file_name
        )
        if not os.path.exists(file_path):
            raise ProcessModelFileNotFoundError(
                f"No file found with name {file_name} in {process_model_info.display_name}"
            )
        with open(file_path, "rb") as f_handle:
            spec_file_data = f_handle.read()
        return spec_file_data

    @staticmethod
    def file_path(spec: ProcessModelInfo, file_name: str) -> str:
        """File_path."""
        return os.path.join(SpecFileService.workflow_path(spec), file_name)

    @staticmethod
    def last_modified(spec: ProcessModelInfo, file_name: str) -> datetime:
        """Last_modified."""
        path = SpecFileService.file_path(spec, file_name)
        return FileSystemService._last_modified(path)

    @staticmethod
    def timestamp(spec: ProcessModelInfo, file_name: str) -> float:
        """Timestamp."""
        path = SpecFileService.file_path(spec, file_name)
        return FileSystemService._timestamp(path)

    @staticmethod
    def delete_file(spec: ProcessModelInfo, file_name: str) -> None:
        """Delete_file."""
        # Fixme: Remember to remove the lookup files when the spec file is removed.
        # lookup_files = session.query(LookupFileModel).filter_by(file_model_id=file_id).all()
        # for lf in lookup_files:
        #     session.query(LookupDataModel).filter_by(lookup_file_model_id=lf.id).delete()
        #     session.query(LookupFileModel).filter_by(id=lf.id).delete()
        # file_path = SpecFileService.file_path(spec, file_name)
        file_path = os.path.join(FileSystemService.root_path(), spec.id, file_name)
        os.remove(file_path)

    @staticmethod
    def delete_all_files(spec: ProcessModelInfo) -> None:
        """Delete_all_files."""
        dir_path = SpecFileService.workflow_path(spec)
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)


    # fixme: Place all the caching stuff in a different service.


    @staticmethod
    def update_process_cache(ref: SpecReference) -> None:
        process_id_lookup = SpecReferenceCache.query.filter_by(identifier=ref.identifier).first()
        if process_id_lookup is None:
            process_id_lookup = SpecReferenceCache(
                identifier=ref.identifier,
                display_name=ref.display_name,
                process_model_id=ref.process_model_id,
                type=ref.type,
                file_name=ref.file_name,
                has_lanes=ref.has_lanes,
                is_executable=ref.is_executable,
                is_primary=ref.is_primary,
                relative_path=ref.relative_path,
            )
            db.session.add(process_id_lookup)
        else:
            if ref.relative_path != process_id_lookup.relative_path:
                full_bpmn_file_path = SpecFileService.full_path_from_relative_path(
                    process_id_lookup.relative_path
                )
                # if the old relative bpmn file no longer exists, then assume things were moved around
                # on the file system. Otherwise, assume it is a duplicate process id and error.
                if os.path.isfile(full_bpmn_file_path):
                    raise ValidationException(
                        f"Process id ({ref.identifier}) has already been used for "
                        f"{process_id_lookup.relative_path}. It cannot be reused."
                    )
                else:
                    process_id_lookup.relative_path = (
                        ref.relative_path
                    )
                    db.session.add(process_id_lookup)
                    db.session.commit()



    @staticmethod
    def update_message_cache(ref: SpecReference) -> None:
        """Assure we have a record in the database of all possible message ids and names."""
        for message_model_identifier in ref.messages.keys():
            message_model = MessageModel.query.filter_by(identifier=message_model_identifier).first()
            if message_model is None:
                message_model = MessageModel(
                    identifier=message_model_identifier, name=ref.messages[message_model_identifier]
                )
                db.session.add(message_model)
                db.session.commit()

    @staticmethod
    def update_message_trigger_cache(ref: SpecReference, process_model_info: ProcessModelInfo) -> None:
        """assure we know which messages can trigger the start of a process."""
        for message_model_identifier in ref.start_messages:
                message_model = MessageModel.query.filter_by(
                    identifier=message_model_identifier
                ).first()
                if message_model is None:
                    raise ValidationException(
                        f"Could not find message model with identifier '{message_model_identifier}'"
                        f"Required by a Start Event in : {ref.file_name}"
                    )
                message_triggerable_process_model = (
                    MessageTriggerableProcessModel.query.filter_by(
                        message_model_id=message_model.id,
                    ).first()
                )

                if message_triggerable_process_model is None:
                    message_triggerable_process_model = (
                        MessageTriggerableProcessModel(
                            message_model_id=message_model.id,
                            process_model_identifier=process_model_info.id,
                            process_group_identifier="process_group_identifier"
                        )
                    )
                    db.session.add(message_triggerable_process_model)
                    db.session.commit()
                else:
                    if (
                        message_triggerable_process_model.process_model_identifier
                        != process_model_info.id
                        # or message_triggerable_process_model.process_group_identifier
                        # != process_model_info.process_group_id
                    ):
                        raise ValidationException(
                            f"Message model is already used to start process model {process_model_info.id}"
                        )

    @staticmethod
    def update_correlation_cache(ref: SpecReference) -> None:
        for correlation_identifier in ref.correlations.keys():
            correlation_property_retrieval_expressions = \
                ref.correlations[correlation_identifier]['retrieval_expressions']

            for cpre in correlation_property_retrieval_expressions:
                message_model_identifier = cpre["messageRef"]
                message_model = MessageModel.query.filter_by(identifier=message_model_identifier).first()
                if message_model is None:
                    raise ValidationException(
                        f"Could not find message model with identifier '{message_model_identifier}'"
                        f"specified by correlation property: {cpre}"
                    )
                # fixme:  I think we are currently ignoring the correction properties.
                message_correlation_property = (
                    MessageCorrelationPropertyModel.query.filter_by(
                        identifier=correlation_identifier,
                        message_model_id=message_model.id,
                    ).first()
                )
                if message_correlation_property is None:
                    message_correlation_property = MessageCorrelationPropertyModel(
                        identifier=correlation_identifier,
                        message_model_id=message_model.id,
                    )
                    db.session.add(message_correlation_property)
                    db.session.commit()
