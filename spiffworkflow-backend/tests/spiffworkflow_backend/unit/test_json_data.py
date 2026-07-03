import json
from hashlib import sha256

import pytest

from spiffworkflow_backend.models.json_data import JsonDataModel


def test_json_data_dict_from_dict_handles_mixed_string_and_integer_keys() -> None:
    data = {
        "validation_results": {
            1: {"valid": True},
            "2": {"valid": False},
        },
        "nested_list": [
            {
                3: "three",
                "4": "four",
            }
        ],
    }

    json_data_dict = JsonDataModel.json_data_dict_from_dict(data)

    expected_data = {
        "validation_results": {
            "1": {"valid": True},
            "2": {"valid": False},
        },
        "nested_list": [
            {
                "3": "three",
                "4": "four",
            }
        ],
    }
    expected_hash = sha256(json.dumps(expected_data, sort_keys=True).encode("utf8")).hexdigest()

    assert json_data_dict == {"hash": expected_hash, "data": expected_data}


def test_json_data_hash_treats_integer_keys_like_json_object_keys() -> None:
    int_key_data = {1: "one"}
    string_key_data = {"1": "one"}

    assert JsonDataModel.json_data_dict_from_dict(int_key_data) == JsonDataModel.json_data_dict_from_dict(string_key_data)


def test_json_data_dict_from_dict_rejects_normalized_key_collisions() -> None:
    with pytest.raises(ValueError, match="JSON object key collision after normalization"):
        JsonDataModel.json_data_dict_from_dict({1: "integer", "1": "string"})
