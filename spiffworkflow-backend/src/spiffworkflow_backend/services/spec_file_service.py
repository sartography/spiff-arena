"""Spec_file_service."""
import os
import shutil
from datetime import datetime
from typing import Any
from typing import List
from typing import Optional

from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db
from lxml import etree  # type: ignore
from lxml.etree import _Element  # type: ignore
from lxml.etree import Element as EtreeElement
from SpiffWorkflow.bpmn.parser.ValidationException import ValidationException  # type: ignore

from spiffworkflow_backend.models.bpmn_process_id_lookup import BpmnProcessIdLookup
from spiffworkflow_backend.models.file import File
from spiffworkflow_backend.models.file import FileReference
from spiffworkflow_backend.models.file import FileType
from spiffworkflow_backend.models.message_correlation_property import (
    MessageCorrelationPropertyModel,
)
from spiffworkflow_backend.models.message_model import MessageModel
from spiffworkflow_backend.models.message_triggerable_process_model import (
    MessageTriggerableProcessModel,
)
from spiffworkflow_backend.models.process_model import ProcessModelInfo
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
        path = SpecFileService.workflow_path(process_model_info)
        files = SpecFileService._get_files(path, file_name)
        if extension_filter != "":
            files = list(
                filter(lambda file: file.name.endswith(extension_filter), files)
            )
        return files

    @staticmethod
    def get_references_for_file(
        file: File, process_model_info: ProcessModelInfo, parser_class: Any
    ) -> list[FileReference]:
        """Uses spiffworkflow to parse BPMN and DMN files to determine how they can be externally referenced.

        Returns a list of Reference objects that contain the type of reference, the id, the name.
        Ex.
        id = {str} 'Level3'
        name = {str} 'Level 3'
        type = {str} 'process'
        """
        references: list[FileReference] = []
        file_path = SpecFileService.file_path(process_model_info, file.name)
        parser = parser_class()
        parser_type = None
        sub_parser = None
        if file.type == FileType.bpmn.value:
            parser.add_bpmn_file(file_path)
            parser_type = "process"
            sub_parsers = list(parser.process_parsers.values())
        elif file.type == FileType.dmn.value:
            parser.add_dmn_file(file_path)
            sub_parsers = list(parser.dmn_parsers.values())
            parser_type = "decision"
        else:
            return references
        for sub_parser in sub_parsers:
            references.append(
                FileReference(
                    id=sub_parser.get_id(), name=sub_parser.get_name(), type=parser_type
                )
            )
        return references

    @staticmethod
    def add_file(
        process_model_info: ProcessModelInfo, file_name: str, binary_data: bytes
    ) -> File:
        """Add_file."""
        # Same as update
        return SpecFileService.update_file(process_model_info, file_name, binary_data)

    @staticmethod
    def update_file(
        process_model_info: ProcessModelInfo, file_name: str, binary_data: bytes
    ) -> File:
        """Update_file."""
        SpecFileService.assert_valid_file_name(file_name)
        file_path = SpecFileService.file_path(process_model_info, file_name)
        SpecFileService.write_file_data_to_system(file_path, binary_data)
        file = SpecFileService.to_file_object(file_name, file_path)

        if file.type == FileType.bpmn.value:
            set_primary_file = False
            if (
                process_model_info.primary_file_name is None
                or file_name == process_model_info.primary_file_name
            ):
                # If no primary process exists, make this primary process.
                set_primary_file = True
            SpecFileService.process_bpmn_file(
                process_model_info,
                file_name,
                binary_data,
                set_primary_file=set_primary_file,
            )

        return file

    @staticmethod
    def get_data(process_model_info: ProcessModelInfo, file_name: str) -> bytes:
        """Get_data."""
        file_path = SpecFileService.file_path(process_model_info, file_name)
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
        file_path = SpecFileService.file_path(spec, file_name)
        os.remove(file_path)

    @staticmethod
    def delete_all_files(spec: ProcessModelInfo) -> None:
        """Delete_all_files."""
        dir_path = SpecFileService.workflow_path(spec)
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)

    @staticmethod
    def get_etree_element_from_file_name(
        process_model_info: ProcessModelInfo, file_name: str
    ) -> EtreeElement:
        """Get_etree_element_from_file_name."""
        binary_data = SpecFileService.get_data(process_model_info, file_name)
        return SpecFileService.get_etree_element_from_binary_data(
            binary_data, file_name
        )

    @staticmethod
    def get_etree_element_from_binary_data(
        binary_data: bytes, file_name: str
    ) -> EtreeElement:
        """Get_etree_element_from_binary_data."""
        try:
            return etree.fromstring(binary_data)
        except etree.XMLSyntaxError as xse:
            raise ApiError(
                "invalid_xml",
                "Failed to parse xml: " + str(xse),
                file_name=file_name,
            ) from xse

    @staticmethod
    def process_bpmn_file(
        process_model_info: ProcessModelInfo,
        file_name: str,
        binary_data: Optional[bytes] = None,
        set_primary_file: Optional[bool] = False,
    ) -> None:
        """Set_primary_bpmn."""
        # If this is a BPMN, extract the process id, and determine if it is contains swim lanes.
        extension = SpecFileService.get_extension(file_name)
        file_type = FileType[extension]
        if file_type == FileType.bpmn:
            if not binary_data:
                binary_data = SpecFileService.get_data(process_model_info, file_name)

            bpmn_etree_element: EtreeElement = (
                SpecFileService.get_etree_element_from_binary_data(
                    binary_data, file_name
                )
            )

            try:
                if set_primary_file:
                    attributes_to_update = {
                        "primary_process_id": (
                            SpecFileService.get_bpmn_process_identifier(
                                bpmn_etree_element
                            )
                        ),
                        "primary_file_name": file_name,
                        "is_review": SpecFileService.has_swimlane(bpmn_etree_element),
                    }
                    ProcessModelService().update_spec(
                        process_model_info, attributes_to_update
                    )

                SpecFileService.check_for_message_models(
                    bpmn_etree_element, process_model_info
                )
                SpecFileService.store_bpmn_process_identifiers(
                    process_model_info, file_name, bpmn_etree_element
                )

            except ValidationException as ve:
                if ve.args[0].find("No executable process tag found") >= 0:
                    raise ApiError(
                        error_code="missing_executable_option",
                        message="No executable process tag found. Please make sure the Executable option is set in the workflow.",
                    ) from ve
                else:
                    raise ApiError(
                        error_code="validation_error",
                        message=f"There was an error validating your workflow. Original message is: {ve}",
                    ) from ve
        else:
            raise ApiError(
                "invalid_xml",
                "Only a BPMN can be the primary file.",
                file_name=file_name,
            )

    @staticmethod
    def has_swimlane(et_root: _Element) -> bool:
        """Look through XML and determine if there are any lanes present that have a label."""
        elements = et_root.xpath(
            "//bpmn:lane",
            namespaces={"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"},
        )
        retval = False
        for el in elements:
            if el.get("name"):
                retval = True
        return retval

    @staticmethod
    def append_identifier_of_process_to_array(
        process_element: _Element, process_identifiers: list[str]
    ) -> None:
        """Append_identifier_of_process_to_array."""
        process_id_key = "id"
        if "name" in process_element.attrib:
            process_id_key = "name"

        process_identifiers.append(process_element.attrib[process_id_key])

    @staticmethod
    def get_all_bpmn_process_identifiers_for_process_model(
        process_model_info: ProcessModelInfo,
    ) -> list[str]:
        """Get_all_bpmn_process_identifiers_for_process_model."""
        if process_model_info.primary_file_name is None:
            return []

        binary_data = SpecFileService.get_data(
            process_model_info, process_model_info.primary_file_name
        )

        et_root: EtreeElement = SpecFileService.get_etree_element_from_binary_data(
            binary_data, process_model_info.primary_file_name
        )
        process_identifiers: list[str] = []
        for child in et_root:
            if child.tag.endswith("process") and child.attrib.get(
                "isExecutable", False
            ):
                subprocesses = child.xpath(
                    "//bpmn:subProcess",
                    namespaces={"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"},
                )
                for subprocess in subprocesses:
                    SpecFileService.append_identifier_of_process_to_array(
                        subprocess, process_identifiers
                    )

                SpecFileService.append_identifier_of_process_to_array(
                    child, process_identifiers
                )

        if len(process_identifiers) == 0:
            raise ValidationException("No executable process tag found")
        return process_identifiers

    @staticmethod
    def get_executable_process_elements(et_root: _Element) -> list[_Element]:
        """Get_executable_process_elements."""
        process_elements = []
        for child in et_root:
            if child.tag.endswith("process") and child.attrib.get(
                "isExecutable", False
            ):
                process_elements.append(child)

        if len(process_elements) == 0:
            raise ValidationException("No executable process tag found")
        return process_elements

    @staticmethod
    def get_executable_bpmn_process_identifiers(et_root: _Element) -> list[str]:
        """Get_executable_bpmn_process_identifiers."""
        process_elements = SpecFileService.get_executable_process_elements(et_root)
        bpmn_process_identifiers = [pe.attrib["id"] for pe in process_elements]
        return bpmn_process_identifiers

    @staticmethod
    def get_bpmn_process_identifier(et_root: _Element) -> str:
        """Get_bpmn_process_identifier."""
        process_elements = SpecFileService.get_executable_process_elements(et_root)

        # There are multiple root elements
        if len(process_elements) > 1:

            # Look for the element that has the startEvent in it
            for e in process_elements:
                this_element: EtreeElement = e
                for child_element in list(this_element):
                    if child_element.tag.endswith("startEvent"):
                        # coorce Any to string
                        return str(this_element.attrib["id"])

            raise ValidationException(
                "No start event found in %s" % et_root.attrib["id"]
            )

        return str(process_elements[0].attrib["id"])

    @staticmethod
    def store_bpmn_process_identifiers(
        process_model_info: ProcessModelInfo, bpmn_file_name: str, et_root: _Element
    ) -> None:
        """Store_bpmn_process_identifiers."""
        relative_process_model_path = SpecFileService.process_model_relative_path(
            process_model_info
        )
        relative_bpmn_file_path = os.path.join(
            relative_process_model_path, bpmn_file_name
        )
        bpmn_process_identifiers = (
            SpecFileService.get_executable_bpmn_process_identifiers(et_root)
        )
        for bpmn_process_identifier in bpmn_process_identifiers:
            process_id_lookup = BpmnProcessIdLookup.query.filter_by(
                bpmn_process_identifier=bpmn_process_identifier
            ).first()
            if process_id_lookup is None:
                process_id_lookup = BpmnProcessIdLookup(
                    bpmn_process_identifier=bpmn_process_identifier,
                    bpmn_file_relative_path=relative_bpmn_file_path,
                )
                db.session.add(process_id_lookup)
                db.session.commit()
            else:
                if relative_bpmn_file_path != process_id_lookup.bpmn_file_relative_path:
                    full_bpmn_file_path = SpecFileService.full_path_from_relative_path(
                        process_id_lookup.bpmn_file_relative_path
                    )
                    # if the old relative bpmn file no longer exists, then assume things were moved around
                    # on the file system. Otherwise, assume it is a duplicate process id and error.
                    if os.path.isfile(full_bpmn_file_path):
                        raise ValidationException(
                            f"Process id ({bpmn_process_identifier}) has already been used for "
                            f"{process_id_lookup.bpmn_file_relative_path}. It cannot be reused."
                        )
                    else:
                        process_id_lookup.bpmn_file_relative_path = (
                            relative_bpmn_file_path
                        )
                        db.session.add(process_id_lookup)
                        db.session.commit()

    @staticmethod
    def check_for_message_models(
        et_root: _Element, process_model_info: ProcessModelInfo
    ) -> None:
        """Check_for_message_models."""
        for child in et_root:
            if child.tag.endswith("message"):
                message_model_identifier = child.attrib.get("id")
                message_name = child.attrib.get("name")
                if message_model_identifier is None:
                    raise ValidationException(
                        "Message identifier is missing from bpmn xml"
                    )

                message_model = MessageModel.query.filter_by(
                    identifier=message_model_identifier
                ).first()
                if message_model is None:
                    message_model = MessageModel(
                        identifier=message_model_identifier, name=message_name
                    )
                    db.session.add(message_model)
                    db.session.commit()

        for child in et_root:
            if child.tag.endswith("}process"):
                message_event_definitions = child.xpath(
                    "//bpmn:startEvent/bpmn:messageEventDefinition",
                    namespaces={"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"},
                )
                if message_event_definitions:
                    message_event_definition = message_event_definitions[0]
                    message_model_identifier = message_event_definition.attrib.get(
                        "messageRef"
                    )
                    if message_model_identifier is None:
                        raise ValidationException(
                            "Could not find messageRef from message event definition: {message_event_definition}"
                        )

                    message_model = MessageModel.query.filter_by(
                        identifier=message_model_identifier
                    ).first()
                    if message_model is None:
                        raise ValidationException(
                            f"Could not find message model with identifier '{message_model_identifier}'"
                            f"specified by message event definition: {message_event_definition}"
                        )

                    message_triggerable_process_model = (
                        MessageTriggerableProcessModel.query.filter_by(
                            message_model_id=message_model.id,
                        ).first()
                    )

                    if message_triggerable_process_model is None:
                        message_triggerable_process_model = MessageTriggerableProcessModel(
                            message_model_id=message_model.id,
                            process_model_identifier=process_model_info.id,
                            process_group_identifier=process_model_info.process_group_id,
                        )
                        db.session.add(message_triggerable_process_model)
                        db.session.commit()
                    else:
                        if (
                            message_triggerable_process_model.process_model_identifier
                            != process_model_info.id
                            or message_triggerable_process_model.process_group_identifier
                            != process_model_info.process_group_id
                        ):
                            raise ValidationException(
                                "Message model is already used to start process model"
                                f"'{process_model_info.process_group_id}/{process_model_info.id}'"
                            )

        for child in et_root:
            if child.tag.endswith("correlationProperty"):
                correlation_identifier = child.attrib.get("id")
                if correlation_identifier is None:
                    raise ValidationException(
                        "Correlation identifier is missing from bpmn xml"
                    )
                correlation_property_retrieval_expressions = child.xpath(
                    "//bpmn:correlationPropertyRetrievalExpression",
                    namespaces={"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"},
                )
                if not correlation_property_retrieval_expressions:
                    raise ValidationException(
                        f"Correlation is missing correlation property retrieval expressions: {correlation_identifier}"
                    )

                for cpre in correlation_property_retrieval_expressions:
                    message_model_identifier = cpre.attrib.get("messageRef")
                    if message_model_identifier is None:
                        raise ValidationException(
                            f"Message identifier is missing from correlation property: {correlation_identifier}"
                        )
                    message_model = MessageModel.query.filter_by(
                        identifier=message_model_identifier
                    ).first()
                    if message_model is None:
                        raise ValidationException(
                            f"Could not find message model with identifier '{message_model_identifier}'"
                            f"specified by correlation property: {cpre}"
                        )
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
