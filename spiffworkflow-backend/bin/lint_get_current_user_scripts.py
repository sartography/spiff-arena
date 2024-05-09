import glob
import os
from typing import NoReturn

from lxml import etree
from spiffworkflow_backend import create_app
from spiffworkflow_backend.services.file_system_service import FileSystemService


def find_script_tasks_with_get_current_user(bpmn_file_path: str, root_path: str) -> None:
    from spiffworkflow_backend.services.spec_file_service import SpecFileService

    try:
        with open(bpmn_file_path, "rb") as bpmn_file:
            binary_data = bpmn_file.read()
        tree = SpecFileService.get_etree_from_xml_bytes(binary_data)
        check_script_and_prescript_elements(tree, bpmn_file_path, root_path)
    except etree.XMLSyntaxError:
        print(f"Error parsing XML in file {bpmn_file_path}. Please check for syntax issues.")
        return


def check_script_and_prescript_elements(tree, bpmn_file_path: str, root_path: str) -> None:
    # Define the namespace map to search for elements
    nsmap = {
        "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
        "spiffworkflow": "http://spiffworkflow.org/bpmn/schema/1.0/core",
    }
    # Find all script tasks and preScript elements
    script_tasks = tree.xpath("//bpmn:scriptTask", namespaces=nsmap)
    pre_scripts = tree.xpath("//spiffworkflow:preScript", namespaces=nsmap)

    # Check script tasks for get_current_user() calls
    for task in script_tasks:
        script = task.find("bpmn:script", namespaces=nsmap)
        if script is not None and script.text is not None and "get_current_user()" in script.text:
            relative_path = os.path.relpath(bpmn_file_path, root_path)
            print(f'Found get_current_user() in script task {task.get("id")} of file {relative_path}')

    # Check preScript elements for get_current_user() calls
    check_scripts_for_get_current_user(pre_scripts, bpmn_file_path, "preScript", root_path)
    post_scripts = tree.xpath("//spiffworkflow:postScript", namespaces=nsmap)
    check_scripts_for_get_current_user(post_scripts, bpmn_file_path, "postScript", root_path)


def check_scripts_for_get_current_user(scripts, bpmn_file_path: str, script_type: str, root_path: str) -> None:
    for script in scripts:
        if script is not None and script.text is not None and "get_current_user()" in script.text:
            # Get the parent of the parent to find the actual BPMN element
            parent = script.getparent().getparent()
            relative_path = os.path.relpath(bpmn_file_path, root_path)
            tag_without_namespace = etree.QName(parent.tag).localname
            if tag_without_namespace not in ["manualTask", "userTask"]:
                print(
                    f"Found get_current_user() in {script_type} of {tag_without_namespace} "
                    f"with id {parent.get('id')} in file {relative_path}"
                )


def main() -> NoReturn:
    app = create_app()
    with app.app_context():
        hot_dir = FileSystemService.root_path()
        # Search for BPMN files and check for get_current_user() calls in script tasks
        bpmn_files = glob.glob(os.path.expanduser(f"{hot_dir}/**/*.bpmn"), recursive=True)

        for bpmn_file in bpmn_files:
            parent_directory = os.path.dirname(bpmn_file)
            # check if parent directory contains a file named 'extension_uischema.json'
            # in which case it's an extension, and it is not necessary to include in this analysis, since
            # extensions typically run using nonpersistent process instances, and therefore have no
            # running-in-background type issues.
            if parent_directory and not os.path.exists(f"{parent_directory}/extension_uischema.json"):
                find_script_tasks_with_get_current_user(bpmn_file, hot_dir)


if __name__ == "__main__":
    main()
