from __future__ import annotations

import json
from hashlib import sha256
from typing import TypedDict

from flask import current_app
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db

#
# class JsonDataModelNotFoundError(Exception):
#     pass
#
#


class KeyedJsonDataDict(TypedDict):
    key: str
    hash: str
    data: dict


class KeyedJsonDataModel(SpiffworkflowBaseDBModel):
    __tablename__ = "keyed_json_data"
    # id: int = db.Column(db.Integer, primary_key=True)

    # this is a sha256 hash of spec and serializer_version
    hash: str = db.Column(db.String(255), nullable=False, unique=True, primary_key=True)
    key: str = db.Column(db.String(255), nullable=False)
    data: dict = db.Column(db.JSON, nullable=False)

    #
    # @classmethod
    # def find_object_by_hash(cls, hash: str) -> JsonDataModel:
    #     json_data_model: JsonDataModel | None = JsonDataModel.query.filter_by(hash=hash).first()
    #     if json_data_model is None:
    #         raise JsonDataModelNotFoundError(f"Could not find a json data model entry with hash: {hash}")
    #     return json_data_model
    #
    # @classmethod
    # def find_data_dict_by_hash(cls, hash: str) -> dict:
    #     return cls.find_object_by_hash(hash).data
    #
    # @classmethod
    # def insert_or_update_json_data_records(cls, json_data_hash_to_json_data_dict_mapping: dict[str, JsonDataDict]) -> None:
    #     list_of_dicts = [*json_data_hash_to_json_data_dict_mapping.values()]
    #     if len(list_of_dicts) > 0:
    #         on_duplicate_key_stmt = None
    #         if current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "mysql":
    #             insert_stmt = mysql_insert(JsonDataModel).values(list_of_dicts)
    #             on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(data=insert_stmt.inserted.data)
    #         else:
    #             insert_stmt = postgres_insert(JsonDataModel).values(list_of_dicts)
    #             on_duplicate_key_stmt = insert_stmt.on_conflict_do_nothing(index_elements=["hash"])
    #         db.session.execute(on_duplicate_key_stmt)
    #
    # @classmethod
    # def insert_or_update_json_data_dict(cls, json_data_dict: JsonDataDict) -> None:
    #     cls.insert_or_update_json_data_records({json_data_dict["hash"]: json_data_dict})
    #
    # @classmethod
    # def create_and_insert_json_data_from_dict(cls, data: dict) -> str:
    #     json_data_dict = cls.json_data_dict_from_dict(data)
    #     cls.insert_or_update_json_data_dict(json_data_dict)
    #     return json_data_dict["hash"]

    @classmethod
    def keyed_json_data_dict_from_dict(cls, full_data: dict) -> dict[str, KeyedJsonDataDict]:
        return_dict: dict[str, KeyedJsonDataDict] = {}
        for key, data in full_data.items():
            full_value = {key: data}
            task_data_json = json.dumps(full_value, sort_keys=True)
            task_data_hash: str = sha256(task_data_json.encode("utf8")).hexdigest()
            return_dict[task_data_hash] = {"key": key, "data": data, "hash": task_data_hash}
        return return_dict
