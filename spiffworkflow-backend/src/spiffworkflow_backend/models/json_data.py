from __future__ import annotations

import json
from hashlib import sha256
from typing import TypedDict

from flask import current_app
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


class JsonDataModelNotFoundError(Exception):
    pass


class JsonDataDict(TypedDict):
    hash: str
    data: dict


# delta algorithm <- just to save it for when we want to try to implement it:
#   a = {"hey": { "hey2": 2, "hey3": 3, "hey6": 7 }, "hey30": 3, "hey40": 4}
#   b = {"hey": { "hey2": 4, "hey5": 3 }, "hey20": 2, "hey30": 3}
#   a_keys = set(a.keys())
#   b_keys = set(b.keys())
#   removed = a_keys - b_keys
#   added_keys = b_keys - a_keys
#   keys_present_in_both = a_keys & b_keys
#   changed = {}
#   for key_in_both in keys_present_in_both:
#       if a[key_in_both] != b[key_in_both]:
#           changed[key_in_both] = b[key_in_both]
#   added = {}
#   for added_key in added_keys:
#       added[added_key] = b[added_key]
#   final_tuple = [added, removed, changed]


# to find the users of this model run:
#   grep -R '_data_hash: ' src/spiffworkflow_backend/models/
class JsonDataModel(SpiffworkflowBaseDBModel):
    __tablename__ = "json_data"
    # id: int = db.Column(db.Integer, primary_key=True)

    # this is a sha256 hash of spec and serializer_version
    hash: str = db.Column(db.String(255), nullable=False, unique=True, primary_key=True)
    data: dict = db.Column(db.JSON, nullable=False)

    @classmethod
    def find_object_by_hash(cls, hash: str) -> JsonDataModel:
        json_data_model: JsonDataModel | None = JsonDataModel.query.filter_by(hash=hash).first()
        if json_data_model is None:
            raise JsonDataModelNotFoundError(f"Could not find a json data model entry with hash: {hash}")
        return json_data_model

    @classmethod
    def find_data_dict_by_hash(cls, hash: str) -> dict:
        return cls.find_object_by_hash(hash).data

    @classmethod
    def insert_or_update_json_data_records(cls, json_data_hash_to_json_data_dict_mapping: dict[str, JsonDataDict]) -> None:
        list_of_dicts = [*json_data_hash_to_json_data_dict_mapping.values()]
        if len(list_of_dicts) > 0:
            on_duplicate_key_stmt = None
            if current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "mysql":
                insert_stmt = mysql_insert(JsonDataModel).values(list_of_dicts)
                on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(hash=insert_stmt.inserted.hash)
            else:
                insert_stmt = postgres_insert(JsonDataModel).values(list_of_dicts)
                on_duplicate_key_stmt = insert_stmt.on_conflict_do_nothing(index_elements=["hash"])
            db.session.execute(on_duplicate_key_stmt)

    @classmethod
    def insert_or_update_json_data_dict(cls, json_data_dict: JsonDataDict) -> None:
        cls.insert_or_update_json_data_records({json_data_dict["hash"]: json_data_dict})

    @classmethod
    def create_and_insert_json_data_from_dict(cls, data: dict) -> str:
        json_data_dict = cls.json_data_dict_from_dict(data)
        cls.insert_or_update_json_data_dict(json_data_dict)
        return json_data_dict["hash"]

    @classmethod
    def json_data_dict_from_dict(cls, data: dict) -> JsonDataDict:
        task_data_json = json.dumps(data, sort_keys=True)
        task_data_hash: str = sha256(task_data_json.encode("utf8")).hexdigest()
        json_data_dict: JsonDataDict = {"hash": task_data_hash, "data": data}
        return json_data_dict
