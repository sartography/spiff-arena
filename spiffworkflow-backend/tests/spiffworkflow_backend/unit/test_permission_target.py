"""Process Model."""
import pytest
from flask.app import Flask
from flask_bpmn.models.db import db
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

from spiffworkflow_backend.models.permission_target import (
    InvalidPermissionTargetUriError,
)
from spiffworkflow_backend.models.permission_target import PermissionTargetModel


class TestPermissionTarget(BaseTest):
    """TestPermissionTarget."""

    def test_wildcard_must_go_at_the_end_of_uri(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_wildcard_must_go_at_the_end_of_uri."""
        permission_target = PermissionTargetModel(uri="/test_group/%")
        db.session.add(permission_target)
        db.session.commit()

        permission_target = PermissionTargetModel(uri="/test_group")
        db.session.add(permission_target)
        db.session.commit()

        with pytest.raises(InvalidPermissionTargetUriError) as exception:
            PermissionTargetModel(uri="/test_group/%/model")
        assert (
            str(exception.value) == "Wildcard must appear at end: /test_group/%/model"
        )

    def test_can_change_asterisk_to_percent_on_creation(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_can_change_asterisk_to_percent_on_creation."""
        permission_target = PermissionTargetModel(uri="/test_group/*")
        db.session.add(permission_target)
        db.session.commit()
        assert isinstance(permission_target.id, int)
        assert permission_target.uri == "/test_group/%"
