from __future__ import annotations

import gzip
import json
from hashlib import sha256
from typing import TypedDict

from flask import current_app
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


class CompressedDataModelNotFoundError(Exception):
    pass


class CompressedDataDict(TypedDict):
    hash: str
    compressed_data: bytes


# to find the users of this model run:
#   grep -R '_data_hash: ' src/spiffworkflow_backend/models/
class CompressedDataModel(SpiffworkflowBaseDBModel):
    __tablename__ = "compressed_data"

    hash: str = db.Column(db.String(255), nullable=False, unique=True, primary_key=True)
    compressed_data: bytes = db.Column(db.BLOB, nullable=False)

    def decompress_data(self) -> str:
        return gzip.decompress(self.compressed_data).decode("utf-8")

    def data_dict(self) -> dict:
        data = self.decompress_data()
        return_dict: dict = json.loads(data)
        return return_dict

    @classmethod
    def find_object_by_hash(cls, hash: str) -> CompressedDataModel:
        compressed_data_model: CompressedDataModel | None = CompressedDataModel.query.filter_by(hash=hash).first()
        if compressed_data_model is None:
            raise CompressedDataModelNotFoundError(f"Could not find a compressed data model entry with hash: {hash}")
        return compressed_data_model

    @classmethod
    def find_data_by_hash(cls, hash: str) -> str:
        compressed_data = cls.find_object_by_hash(hash).compressed_data
        return gzip.decompress(compressed_data).decode("utf-8")

    @classmethod
    def find_data_dict_by_hash(cls, hash: str) -> dict:
        data_string = cls.find_data_by_hash(hash)
        return_dict: dict = json.loads(data_string)
        return return_dict

    @classmethod
    def insert_or_update_compressed_data_records(
        cls, compressed_data_hash_to_compressed_data_dict_mapping: dict[str, CompressedDataDict]
    ) -> None:
        list_of_dicts = [*compressed_data_hash_to_compressed_data_dict_mapping.values()]
        if len(list_of_dicts) > 0:
            on_duplicate_key_stmt = None
            if current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "mysql":
                insert_stmt = mysql_insert(CompressedDataModel).values(list_of_dicts)
                on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(compressed_data=insert_stmt.inserted.compressed_data)
            else:
                insert_stmt = postgres_insert(CompressedDataModel).values(list_of_dicts)
                on_duplicate_key_stmt = insert_stmt.on_conflict_do_nothing(index_elements=["hash"])
            db.session.execute(on_duplicate_key_stmt)

    @classmethod
    def insert_or_update_compressed_data_dict(cls, compressed_data_dict: CompressedDataDict) -> None:
        cls.insert_or_update_compressed_data_records({compressed_data_dict["hash"]: compressed_data_dict})

    @classmethod
    def create_and_insert_compressed_data_from_dict(cls, data: dict) -> str:
        compressed_data_dict = cls.compressed_data_dict_from_dict(data)
        cls.insert_or_update_compressed_data_dict(compressed_data_dict)
        return compressed_data_dict["hash"]

    @classmethod
    def compressed_data_dict_from_dict(cls, data: dict) -> CompressedDataDict:
        task_data_json = json.dumps(data, sort_keys=True)
        task_data_compressed = gzip.compress(task_data_json.encode("utf8"))
        task_data_hash: str = sha256(task_data_compressed).hexdigest()
        compressed_data_dict: CompressedDataDict = {
            "hash": task_data_hash,
            "compressed_data": task_data_compressed,
        }
        return compressed_data_dict
