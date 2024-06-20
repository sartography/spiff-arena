import json
import sys

from spiffworkflow_backend import create_app


def main() -> None:
    app = create_app()
    task_data_json_file = sys.argv[1]
    python_variable_file = f"{task_data_json_file}_output.py"

    with app.app_context():
        contents = None
        with open(task_data_json_file) as file:
            contents = json.load(file)

        with open(python_variable_file, "w") as file:
            for key, value in contents.items():
                file.write(f"{key} = {repr(value)}\n")


if len(sys.argv) < 2:
    raise Exception("A task data json file must be provided")

if __name__ == "__main__":
    main()
