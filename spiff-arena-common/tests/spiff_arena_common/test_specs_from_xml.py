from spiff_arena_common.runner import specs_from_xml


no_processes = ("no_processes.bpmn", """
<bpmn:definitions
  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  id="Definitions_no_processes"
  targetNamespace="http://bpmn.io/schema/bpmn">
</bpmn:definitions>
""")

not_executable = ("not_executable.bpmn", """
<bpmn:definitions
  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  id="Definitions_not_executable"
  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_NotExecutable" isExecutable="false">
    <bpmn:startEvent id="StartEvent_1" />
  </bpmn:process>
</bpmn:definitions>
""")


def test_specs_from_xml_reports_missing_processes():
    specs, err = specs_from_xml([no_processes])

    assert specs is None
    assert err == "No BPMN process definitions were found in the XML."


def test_specs_from_xml_reports_non_executable_processes():
    specs, err = specs_from_xml([not_executable])

    assert specs is None
    assert err == (
        "No executable BPMN process definitions were found in the XML. "
        "Found non-executable processes: Process_NotExecutable."
    )
