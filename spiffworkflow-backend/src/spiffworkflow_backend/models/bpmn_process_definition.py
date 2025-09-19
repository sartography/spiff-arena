from __future__ import annotations

import copy
from dataclasses import dataclass

from flask import current_app
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects import mysql
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


# contents of top-level attributes from spiff:
#   "subprocess_specs",
#   "spec",
#
# each subprocess will have its own row in this table.
# there is a join table to link them together: bpmn_process_definition_relationship
@dataclass
class BpmnProcessDefinitionModel(SpiffworkflowBaseDBModel):
    __tablename__ = "bpmn_process_definition"
    __table_args__ = (
        UniqueConstraint(
            "full_process_model_hash",
            "single_process_hash",
            name="process_hash_unique",
        ),
    )

    id: int = db.Column(db.Integer, primary_key=True)

    # this is a sha256 hash of spec and serializer_version
    # note that a call activity is its own row in this table, with its own hash,
    # and therefore it only gets stored once per version, and can be reused
    # by multiple calling processes.
    single_process_hash: str = db.Column(db.String(255), nullable=False)

    # only the top level parent will have this set
    # it includes all subprocesses and call activities
    full_process_model_hash: str | None = db.Column(db.String(255), nullable=True, unique=True)

    bpmn_identifier: str = db.Column(db.String(255), nullable=False, index=True)
    bpmn_name: str = db.Column(db.String(255), nullable=True, index=True)

    properties_json: dict = db.Column(db.JSON, nullable=False)

    # TODO: remove these from process_instance
    bpmn_version_control_type: str = db.Column(db.String(50))
    bpmn_version_control_identifier: str = db.Column(db.String(255))

    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)

    @classmethod
    def keys_for_full_process_model_hash(cls) -> list[str]:
        return ["spec", "subprocess_specs", "serializer_version"]

    @classmethod
    def insert_or_update_record(cls, bpmn_process_definition_dict: dict) -> None:
        new_stuff = {"bpmn_identifier": bpmn_process_definition_dict["bpmn_identifier"]}
        on_duplicate_key_stmt = None
        print("HEYYYYYYYYY")
        if current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "mysql":
            insert_stmt = mysql_insert(BpmnProcessDefinitionModel).values(bpmn_process_definition_dict)
            on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(**new_stuff)
            print("IN BPMN")
            print(on_duplicate_key_stmt.compile(dialect=mysql.dialect()))
            # on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            #     full_process_model_hash=insert_stmt.inserted.full_process_model_hash
            # )
        else:
            insert_stmt = postgres_insert(BpmnProcessDefinitionModel).values(bpmn_process_definition_dict)
            on_duplicate_key_stmt = insert_stmt.on_conflict_do_nothing(index_elements=["full_process_model_hash"])
        return db.session.execute(on_duplicate_key_stmt)
