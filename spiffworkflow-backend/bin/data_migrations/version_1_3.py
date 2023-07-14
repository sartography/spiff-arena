import json
import os
import uuid
from hashlib import sha256

from spiffworkflow_backend import create_app
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel


class VersionOneThree:
    def run(self) -> None:
        os.environ["SPIFFWORKFLOW_BACKEND_ENV"] = "local_development"
        if os.environ.get("SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR") is None:
            os.environ["SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR"] = "hey"
        flask_env_key = "FLASK_SESSION_SECRET_KEY"
        os.environ[flask_env_key] = "whatevs"
        app = create_app()
        with app.app_context():
            task_definitions = self.get_relevant_task_definitions()
            for task_definition in task_definitions:
                self.process_task_definition(task_definition)
                relating_task_models = TaskModel.query.filter_by(task_definition_id=task_definition.id).all()
                for task_model in relating_task_models:
                    self.process_task_model(task_model, task_definition)
            db.session.commit()

    def get_relevant_task_definitions(self) -> list[TaskDefinitionModel]:
        task_definitions: list[TaskDefinitionModel] = TaskDefinitionModel.query.filter_by(
            typename="_BoundaryEventParent"
        ).all()
        return task_definitions

    def process_task_definition(self, task_definition: TaskDefinitionModel) -> None:
        task_definition.typename = "BoundaryEventSplit"
        task_definition.bpmn_identifier = task_definition.bpmn_identifier.replace(
            "BoundaryEventParent", "BoundaryEventSplit"
        )

        properties_json = task_definition.properties_json
        properties_json.pop("main_child_task_spec")
        properties_json["typename"] = task_definition.typename
        properties_json["name"] = task_definition.bpmn_identifier
        task_definition.properties_json = properties_json
        db.session.add(task_definition)

        join_properties_json = {
            "name": task_definition.bpmn_identifier.replace("BoundaryEventSplit", "BoundaryEventJoin"),
            "manual": False,
            "bpmn_id": None,
            "lookahead": 2,
            "inputs": properties_json["outputs"],
            "outputs": [],
            "split_task": task_definition.bpmn_identifier,
            "threshold": None,
            "cancel": True,
            "typename": "BoundaryEventJoin",
        }

        join_task_definition = TaskDefinitionModel(
            bpmn_process_definition_id=task_definition.bpmn_process_definition_id,
            bpmn_identifier=join_properties_json["name"],
            typename=join_properties_json["typename"],
            properties_json=join_properties_json,
        )
        db.session.add(join_task_definition)

        for parent_bpmn_identifier in properties_json["inputs"]:
            parent_task_definition = TaskDefinitionModel.query.filter_by(
                bpmn_identifier=parent_bpmn_identifier,
                bpmn_process_definition_id=task_definition.bpmn_process_definition_id,
            ).first()
            parent_task_definition.properties_json["outputs"] = [
                name.replace("BoundaryEventParent", "BoundaryEventSplit")
                for name in parent_task_definition.properties_json["outputs"]
            ]
            db.session.add(parent_task_definition)

        for child_bpmn_identifier in properties_json["outputs"]:
            child_task_definition = TaskDefinitionModel.query.filter_by(
                bpmn_identifier=child_bpmn_identifier,
                bpmn_process_definition_id=task_definition.bpmn_process_definition_id,
            ).first()
            child_task_definition.properties_json["outputs"].append(join_task_definition.bpmn_identifier)
            child_task_definition.properties_json["inputs"] = [
                name.replace("BoundaryEventParent", "BoundaryEventSplit")
                for name in child_task_definition.properties_json["inputs"]
            ]
            db.session.add(child_task_definition)

    def process_task_model(self, task_model: TaskModel, task_definition: TaskDefinitionModel) -> None:
        task_model.properties_json["task_spec"] = task_definition.bpmn_identifier
        db.session.add(task_model)

        child_task_models = []
        all_children_completed = True

        # Ruff keeps complaining unless it's done like this
        blank_json = json.dumps("{}")
        blank_json_data_hash = sha256(blank_json.encode("utf8")).hexdigest()

        for child_task_guid in task_model.properties_json["children"]:
            child_task_model = TaskModel.query.filter_by(guid=child_task_guid).first()
            if child_task_model.state not in ["COMPLETED", "CANCELLED"]:
                all_children_completed = False
            child_task_models.append(child_task_model)

        for child_task_model in child_task_models:
            if child_task_model.state == "CANCELLED":
                # Cancelled tasks don't have children
                continue

            new_task_state = None
            start_in_seconds = child_task_model.start_in_seconds
            end_in_seconds = None

            if child_task_model.state in ["MAYBE", "LIKELY", "FUTURE"]:
                new_task_state = child_task_model.state
            elif child_task_model.state in ["WAITING", "READY", "STARTED"]:
                new_task_state = "FUTURUE"
            elif child_task_model.state == "COMPLETED":
                if all_children_completed:
                    new_task_state = "COMPLETED"
                    end_in_seconds = child_task_model.end_in_seconds
                else:
                    new_task_state = "WAITING"
            elif child_task_model.state == "ERROR":
                new_task_state = "WAITING"
            else:
                raise Exception(f"Unknown state: {child_task_model.state} for {child_task_model.guild}")

            new_task_properties_json = {
                "id": str(uuid.uuid4()),
                "parent": child_task_model.guid,
                "children": [],
                "state": new_task_state,
                "task_spec": task_definition.bpmn_identifier.replace("BoundaryEventSplit", "BoundaryEventJoin"),
                "last_state_change": None,
                "triggered": False,
                "internal_data": {},
            }

            new_task_model = TaskModel(
                guid=new_task_properties_json["id"],
                bpmn_process_id=task_model.bpmn_process_id,
                process_instance_id=task_model.process_instance_id,
                task_definition_id=task_model.task_definition_id,
                state=new_task_properties_json["state"],
                properties_json=new_task_properties_json,
                start_in_seconds=start_in_seconds,
                end_in_seconds=end_in_seconds,
                json_data_hash=blank_json_data_hash,
                python_env_data_hash=blank_json_data_hash,
            )
            db.session.add(new_task_model)

            child_task_model.properties_json["children"].append(new_task_model.guid)
            db.session.add(child_task_model)


VersionOneThree().run()
