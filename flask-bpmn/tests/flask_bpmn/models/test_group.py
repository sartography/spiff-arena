"""Test cases for the group module."""
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from flask_bpmn.models.group import FlaskBpmnGroupModel


class AppGroupModel(FlaskBpmnGroupModel):
    """AppGroupModel."""


def test_table_names_are_singular_per_what_appear_to_be_flask_conventions() -> None:
    """Test_is_jsonable_can_succeed."""
    assert FlaskBpmnGroupModel.__tablename__ == "group"


def test__all_subclasses_of_spiffworkflow_base_db_model_returns_all_subclasses_that_are_defined() -> None:
    """Test_is_jsonable_can_succeed."""
    assert SpiffworkflowBaseDBModel._all_subclasses() == [
        FlaskBpmnGroupModel,
        AppGroupModel,
    ]
