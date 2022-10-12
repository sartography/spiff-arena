"""Test cases for the __main__ module."""
import io

from flask_bpmn.api.api_error import ApiError


def test_is_jsonable_can_succeed() -> None:
    """Test_is_jsonable_can_succeed."""
    result = ApiError.is_jsonable("This is a string and should pass json.dumps")
    assert result is True


def test_is_jsonable_can_fail() -> None:
    """Test_is_jsonable_can_fail."""
    result = ApiError.is_jsonable(io.StringIO("BAD JSON OBJECT"))
    assert result is False


def test_remove_unserializeable_from_dict_succeeds() -> None:
    """Test_remove_unserializeable_from_dict_succeeds."""
    initial_dict_object = {
        "valid_key": "valid_value",
        "invalid_key_value": io.StringIO("BAD JSON OBJECT"),
    }
    final_dict_object = {
        "valid_key": "valid_value",
    }
    result = ApiError.remove_unserializeable_from_dict(initial_dict_object)
    assert result == final_dict_object
