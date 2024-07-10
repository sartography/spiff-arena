import glob

from lxml import etree


def detect_multiple_incoming_flows(bpmn_file):
    # Parse the BPMN file
    try:
        # actually use SpecFileService.get_etree_from_xml_bytes if we use this in future
        tree = etree.parse(bpmn_file, parser=etree.XMLParser(resolve_entities=False))  # noqa: S320
    except etree.XMLSyntaxError as e:
        print(f"Error parsing {bpmn_file}: {e}")
        return []

    root = tree.getroot()

    # Namespace dictionary for finding elements
    ns = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}

    # Find all sequence flows
    sequence_flows = root.findall(".//bpmn:sequenceFlow", namespaces=ns)

    # Dictionary to keep track of incoming flows for each target
    incoming_flows = {}

    # Iterate through sequence flows and count incoming flows for each target
    for flow in sequence_flows:
        target_ref = flow.get("targetRef")
        if target_ref in incoming_flows:
            incoming_flows[target_ref] += 1
        else:
            incoming_flows[target_ref] = 1

    # Find tasks with multiple incoming flows, excluding gateways
    tasks_with_multiple_incoming = []
    for element, count in incoming_flows.items():
        if count > 1:
            # Check if the element is a task (not a gateway)
            task_elements = root.findall(f".//*[@id='{element}']", namespaces=ns)
            if task_elements:
                task_element = task_elements[0]
                if not any(tag in task_element.tag for tag in ["Gateway", "Event"]):
                    tasks_with_multiple_incoming.append(element)

    return tasks_with_multiple_incoming


def validate_bpmn_files():
    glob_pattern = "**/*.bpmn"
    # Find all BPMN files matching the glob pattern
    bpmn_files = glob.glob(glob_pattern, recursive=True)

    for bpmn_file in bpmn_files:
        tasks_with_issues = detect_multiple_incoming_flows(bpmn_file)

        if tasks_with_issues:
            print(f"Tasks with multiple incoming sequence flows in {bpmn_file}:")
            for task in tasks_with_issues:
                print(f" - {task}")


# Run the validation
validate_bpmn_files()
