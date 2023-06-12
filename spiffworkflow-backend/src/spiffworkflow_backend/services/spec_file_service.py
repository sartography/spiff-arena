import os
import shutil
from datetime import datetime

from lxml import etree  # type: ignore
from SpiffWorkflow.bpmn.parser.BpmnParser import BpmnValidator  # type: ignore
from spiffworkflow_backend.models.correlation_property_cache import CorrelationPropertyCache
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.file import File
from spiffworkflow_backend.models.file import FileType
from spiffworkflow_backend.models.file import SpecReference
from spiffworkflow_backend.models.message_triggerable_process_model import MessageTriggerableProcessModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.spec_reference import SpecReferenceCache
from spiffworkflow_backend.services.custom_parser import MyCustomParser
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_caller_service import ProcessCallerService
from spiffworkflow_backend.services.process_model_service import ProcessModelService


class ProcessModelFileNotFoundError(Exception):
    pass


class ProcessModelFileInvalidError(Exception):
    pass


class SpecFileService(FileSystemService):

    """We store spec files on the file system. This allows us to take advantage of Git for
    syncing and versioning.
     The files are stored in a directory whose path is determined by the category and spec names.
    """

    @staticmethod
    def get_files(
        process_model_info: ProcessModelInfo,
        file_name: str | None = None,
        extension_filter: str = "",
    ) -> list[File]:
        """Return all files associated with a workflow specification."""
        path = os.path.join(FileSystemService.root_path(), process_model_info.id_for_file_path())
        files = SpecFileService._get_files(path, file_name)
        if extension_filter != "":
            files = list(filter(lambda file: file.name.endswith(extension_filter), files))
        return files

    @staticmethod
    def reference_map(references: list[SpecReference]) -> dict[str, SpecReference]:
        """Creates a dict with provided references organized by id."""
        ref_map = {}
        for ref in references:
            ref_map[ref.identifier] = ref
        return ref_map

    @staticmethod
    def get_references_for_process(
        process_model_info: ProcessModelInfo,
    ) -> list[SpecReference]:
        files = SpecFileService.get_files(process_model_info)
        references = []
        for file in files:
            references.extend(SpecFileService.get_references_for_file(file, process_model_info))
        return references

    @classmethod
    def get_references_for_file(cls, file: File, process_model_info: ProcessModelInfo) -> list[SpecReference]:
        full_file_path = SpecFileService.full_file_path(process_model_info, file.name)
        file_contents: bytes = b""
        with open(full_file_path) as f:
            file_contents = f.read().encode()
        return cls.get_references_for_file_contents(process_model_info, file.name, file_contents)

    @classmethod
    def get_etree_from_xml_bytes(cls, binary_data: bytes) -> etree.Element:
        etree_xml_parser = etree.XMLParser(resolve_entities=False)
        return etree.fromstring(binary_data, parser=etree_xml_parser)  # noqa: S320

    @classmethod
    def get_references_for_file_contents(
        cls, process_model_info: ProcessModelInfo, file_name: str, binary_data: bytes
    ) -> list[SpecReference]:
        """Uses spiffworkflow to parse BPMN and DMN files to determine how they can be externally referenced.

        Returns a list of Reference objects that contain the type of reference, the id, the name.
        Ex.
        id = {str} 'Level3'
        name = {str} 'Level 3'
        type = {str} 'process' / 'decision'
        """
        references: list[SpecReference] = []
        file_path = os.path.join(process_model_info.id_for_file_path(), file_name)
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
                SpecReference(
                    identifier=sub_parser.bpmn_id,
                    display_name=sub_parser.get_name(),
                    process_model_id=process_model_info.id,
                    type=parser_type,
                    file_name=file_name,
                    relative_path=file_path,
                    has_lanes=has_lanes,
                    is_executable=is_executable,
                    messages=messages,
                    is_primary=is_primary,
                    correlations=correlations,
                    start_messages=start_messages,
                    called_element_ids=called_element_ids,
                )
            )
        return references

    @staticmethod
    def add_file(process_model_info: ProcessModelInfo, file_name: str, binary_data: bytes) -> File:
        # Same as update
        return SpecFileService.update_file(process_model_info, file_name, binary_data)

    @classmethod
    def validate_bpmn_xml(cls, file_name: str, binary_data: bytes) -> None:
        file_type = FileSystemService.file_type(file_name)
        if file_type.value == FileType.bpmn.value:
            BpmnValidator()
            parser = MyCustomParser()
            try:
                parser.add_bpmn_xml(cls.get_etree_from_xml_bytes(binary_data), filename=file_name)
            except Exception as exception:
                raise ProcessModelFileInvalidError(
                    f"Received error trying to parse bpmn xml: {str(exception)}"
                ) from exception

    @classmethod
    def update_file(cls, process_model_info: ProcessModelInfo, file_name: str, binary_data: bytes) -> File:
        SpecFileService.assert_valid_file_name(file_name)
        cls.validate_bpmn_xml(file_name, binary_data)

        references = cls.get_references_for_file_contents(process_model_info, file_name, binary_data)
        primary_process_ref = next((ref for ref in references if ref.is_primary and ref.is_executable), None)

        SpecFileService.clear_caches_for_file(file_name, process_model_info)
        for ref in references:
            # If no valid primary process is defined, default to the first process in the
            # updated file.
            if not primary_process_ref and ref.type == "process" and ref.is_executable:
                ref.is_primary = True

            if ref.is_primary:
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
            SpecFileService.update_caches(ref)

        # make sure we save the file as the last thing we do to ensure validations have run
        full_file_path = SpecFileService.full_file_path(process_model_info, file_name)
        SpecFileService.write_file_data_to_system(full_file_path, binary_data)
        return SpecFileService.to_file_object(file_name, full_file_path)

    @staticmethod
    def get_data(process_model_info: ProcessModelInfo, file_name: str) -> bytes:
        full_file_path = SpecFileService.full_file_path(process_model_info, file_name)
        if not os.path.exists(full_file_path):
            raise ProcessModelFileNotFoundError(
                f"No file found with name {file_name} in {process_model_info.display_name}"
            )
        with open(full_file_path, "rb") as f_handle:
            spec_file_data = f_handle.read()
        return spec_file_data

    @staticmethod
    def full_file_path(process_model: ProcessModelInfo, file_name: str) -> str:
        return os.path.abspath(os.path.join(SpecFileService.process_model_full_path(process_model), file_name))

    @staticmethod
    def last_modified(process_model: ProcessModelInfo, file_name: str) -> datetime:
        full_file_path = SpecFileService.full_file_path(process_model, file_name)
        return FileSystemService._last_modified(full_file_path)

    @staticmethod
    def timestamp(process_model: ProcessModelInfo, file_name: str) -> float:
        full_file_path = SpecFileService.full_file_path(process_model, file_name)
        return FileSystemService._timestamp(full_file_path)

    @staticmethod
    def delete_file(process_model: ProcessModelInfo, file_name: str) -> None:
        # Fixme: Remember to remove the lookup files when the process_model file is removed.
        # lookup_files = session.query(LookupFileModel).filter_by(file_model_id=file_id).all()
        # for lf in lookup_files:
        #     session.query(LookupDataModel).filter_by(lookup_file_model_id=lf.id).delete()
        #     session.query(LookupFileModel).filter_by(id=lf.id).delete()
        full_file_path = SpecFileService.full_file_path(process_model, file_name)
        os.remove(full_file_path)

    @staticmethod
    def delete_all_files(process_model: ProcessModelInfo) -> None:
        dir_path = SpecFileService.process_model_full_path(process_model)
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)

    # fixme: Place all the caching stuff in a different service.

    @staticmethod
    def update_caches(ref: SpecReference) -> None:
        SpecFileService.update_process_cache(ref)
        SpecFileService.update_process_caller_cache(ref)
        SpecFileService.update_message_trigger_cache(ref)
        SpecFileService.update_correlation_cache(ref)

    @staticmethod
    def clear_caches_for_file(file_name: str, process_model_info: ProcessModelInfo) -> None:
        """Clear all caches related to a file."""
        records = (
            db.session.query(SpecReferenceCache)
            .filter(SpecReferenceCache.file_name == file_name)
            .filter(SpecReferenceCache.process_model_id == process_model_info.id)
            .all()
        )

        process_ids = []

        for record in records:
            process_ids.append(record.identifier)
            db.session.delete(record)

        ProcessCallerService.clear_cache_for_process_ids(process_ids)
        # fixme:  likely the other caches should be cleared as well, but we don't have a clean way to do so yet.

    @staticmethod
    def clear_caches() -> None:
        db.session.query(SpecReferenceCache).delete()
        ProcessCallerService.clear_cache()
        # fixme:  likely the other caches should be cleared as well, but we don't have a clean way to do so yet.

    @staticmethod
    def update_process_cache(ref: SpecReference) -> None:
        process_id_lookup = (
            SpecReferenceCache.query.filter_by(identifier=ref.identifier).filter_by(type=ref.type).first()
        )
        if process_id_lookup is None:
            process_id_lookup = SpecReferenceCache.from_spec_reference(ref)
            db.session.add(process_id_lookup)
            db.session.commit()
        else:
            if ref.relative_path != process_id_lookup.relative_path:
                full_bpmn_file_path = SpecFileService.full_path_from_relative_path(process_id_lookup.relative_path)
                # if the old relative bpmn file no longer exists, then assume things were moved around
                # on the file system. Otherwise, assume it is a duplicate process id and error.
                if os.path.isfile(full_bpmn_file_path):
                    raise ProcessModelFileInvalidError(
                        f"Process id ({ref.identifier}) has already been used for "
                        f"{process_id_lookup.relative_path}. It cannot be reused."
                    )
                else:
                    process_id_lookup.relative_path = ref.relative_path
                    db.session.add(process_id_lookup)
                    db.session.commit()

    @staticmethod
    def update_process_caller_cache(ref: SpecReference) -> None:
        ProcessCallerService.add_caller(ref.identifier, ref.called_element_ids)

    @staticmethod
    def update_message_trigger_cache(ref: SpecReference) -> None:
        """Assure we know which messages can trigger the start of a process."""
        for message_name in ref.start_messages:
            message_triggerable_process_model = MessageTriggerableProcessModel.query.filter_by(
                message_name=message_name,
            ).first()
            if message_triggerable_process_model is None:
                message_triggerable_process_model = MessageTriggerableProcessModel(
                    message_name=message_name,
                    process_model_identifier=ref.process_model_id,
                )
                db.session.add(message_triggerable_process_model)
                db.session.commit()
            else:
                if message_triggerable_process_model.process_model_identifier != ref.process_model_id:
                    raise ProcessModelFileInvalidError(
                        f"Message model is already used to start process model {ref.process_model_id}"
                    )

    @staticmethod
    def update_correlation_cache(ref: SpecReference) -> None:
        for name in ref.correlations.keys():
            correlation_property_retrieval_expressions = ref.correlations[name]["retrieval_expressions"]

            for cpre in correlation_property_retrieval_expressions:
                message_name = ref.messages.get(cpre["messageRef"], None)
                retrieval_expression = cpre["expression"]
                process_model_id = ref.process_model_id

                existing = CorrelationPropertyCache.query.filter_by(
                    name=name,
                    message_name=message_name,
                    process_model_id=process_model_id,
                    retrieval_expression=retrieval_expression,
                ).first()
                if existing is None:
                    new_cache = CorrelationPropertyCache(
                        name=name,
                        message_name=message_name,
                        process_model_id=process_model_id,
                        retrieval_expression=retrieval_expression,
                    )
                    db.session.add(new_cache)
                    db.session.commit()
