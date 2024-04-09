import glob
import os
from typing import NoReturn

from lxml import etree
from spiffworkflow_backend import create_app


def find_script_tasks_with_get_current_user(bpmn_file_path: str) -> None:
    with open(bpmn_file_path, encoding="utf-8") as bpmn_file:
        try:
            tree = etree.parse(bpmn_file)
        except etree.XMLSyntaxError:
            print(f"Error parsing XML in file {bpmn_file_path}. Please check for syntax issues.")
            return
        check_script_and_prescript_elements(tree, bpmn_file_path)


def check_script_and_prescript_elements(tree, bpmn_file_path: str) -> None:
    # Define the namespace map to search for elements
    nsmap = {
        "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
        "spiffworkflow": "http://spiffworkflow.org/bpmn/schema/1.0/core"
    }
    # Find all script tasks and preScript elements
    script_tasks = tree.xpath("//bpmn:scriptTask", namespaces=nsmap)
    pre_scripts = tree.xpath("//spiffworkflow:preScript", namespaces=nsmap)
    post_scripts = tree.xpath("//spiffworkflow:postScript", namespaces=nsmap)

    # Check script tasks for get_current_user() calls
    for task in script_tasks:
        script = task.find("bpmn:script", namespaces=nsmap)
        if script is not None and script.text is not None and "get_current_user()" in script.text:
            print(f'Found get_current_user() in script task {task.get("id")} of file {bpmn_file_path}')

    # Check preScript elements for get_current_user() calls
    for pre_script in pre_scripts:
        if pre_script is not None and pre_script.text is not None and "get_current_user()" in pre_script.text:
            # Get the parent of the parent to find the actual BPMN element
            parent = pre_script.getparent().getparent()
            if parent.tag != "{http://www.omg.org/spec/BPMN/20100524/MODEL}manualTask" and parent.tag != "{http://www.omg.org/spec/BPMN/20100524/MODEL}userTask":
                print(f'Found get_current_user() in preScript of {parent.tag} with id {parent.get("id")} in file {bpmn_file_path}')
    # Check postScript elements for get_current_user() calls
    for post_script in post_scripts:
        if post_script is not None and post_script.text is not None and "get_current_user()" in post_script.text:
            # Get the parent of the parent to find the actual BPMN element
            parent = post_script.getparent().getparent()
            if parent.tag != "{http://www.omg.org/spec/BPMN/20100524/MODEL}manualTask" and parent.tag != "{http://www.omg.org/spec/BPMN/20100524/MODEL}userTask":
                print(f'Found get_current_user() in postScript of {parent.tag} with id {parent.get("id")} in file {bpmn_file_path}')


def main() -> NoReturn:
    app = create_app()
    with app.app_context():
        # Search for BPMN files and check for get_current_user() calls in script tasks
        bpmn_files = glob.glob(os.path.expanduser("~/projects/github/status-im/process-models/**/*.bpmn"), recursive=True)
        for bpmn_file in bpmn_files:
            find_script_tasks_with_get_current_user(bpmn_file)


if __name__ == "__main__":
    main()
