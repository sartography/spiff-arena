import glob
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
        # Define the namespace map to search for elements
        nsmap = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
        # Find all script tasks
        script_tasks = tree.xpath("//bpmn:scriptTask", namespaces=nsmap)
        for task in script_tasks:
            script = task.find("bpmn:script", namespaces=nsmap)
            if script is not None and "get_current_user()" in script.text:
                print(f'Found get_current_user() in script task {task.get("id")} of file {bpmn_file_path}')


def main() -> NoReturn:
    app = create_app()
    with app.app_context():
        # Search for BPMN files and check for get_current_user() calls in script tasks
        bpmn_files = glob.glob("tests/data/**/*.bpmn", recursive=True)
        for bpmn_file in bpmn_files:
            find_script_tasks_with_get_current_user(bpmn_file)


if __name__ == "__main__":
    main()
