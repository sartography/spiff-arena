from SpiffWorkflow.bpmn.serializer.default.process_spec import BpmnProcessSpecConverter  # type: ignore
from SpiffWorkflow.bpmn.specs.bpmn_process_spec import BpmnProcessSpec  # type: ignore


class BpmnProcessSpecWithDiagramConverter(BpmnProcessSpecConverter):  # type: ignore
    """Keep the parsed diagram with the versioned definition, including across runtime saves.

    The XML participates in the existing definition hashes, so a layout-only edit
    cannot replace another instance's diagram. Older definitions omit the field;
    serializing them must not change their hashes or attach today's XML.
    """

    def to_dict(self, spec: BpmnProcessSpec) -> dict:
        result: dict = super().to_dict(spec)
        if getattr(spec, "bpmn_xml", None) is not None:
            result["bpmn_xml"] = spec.bpmn_xml
        return result

    def from_dict(self, dct: dict) -> BpmnProcessSpec:
        bpmn_xml = dct.pop("bpmn_xml", None)
        spec = super().from_dict(dct)
        if bpmn_xml is not None:
            spec.bpmn_xml = bpmn_xml
        return spec
