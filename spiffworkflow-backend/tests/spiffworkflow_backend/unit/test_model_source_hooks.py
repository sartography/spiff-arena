"""Generic model-source provider dispatch, independent of any extension."""

from unittest.mock import MagicMock
from unittest.mock import Mock

import pytest
from flask import Flask

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.model_sources import ModelSources


def test_without_app_context_uses_repository() -> None:
    assert ModelSources.for_instance(ProcessInstanceModel(id=123)).files is None


def test_without_extension_uses_repository() -> None:
    with Flask(__name__).app_context():
        assert ModelSources.for_instance(ProcessInstanceModel(id=123)).files is None


@pytest.mark.parametrize("files_present", [True, False])
def test_delegates_source_selection_to_provider(files_present: bool) -> None:
    app = Flask(__name__)
    files = MagicMock(spec=["paths", "read", "__bool__"]) if files_present else None
    if files is not None:
        files.__bool__.return_value = False
    provider = Mock(open=Mock(return_value=files))
    app.extensions["model_sources"] = provider
    instance = ProcessInstanceModel(id=123)

    with app.app_context():
        assert ModelSources.for_instance(instance).files is files

    provider.open.assert_called_once_with(db.session, instance)


def test_unsaved_instance_uses_repository_without_opening_provider() -> None:
    app = Flask(__name__)
    provider = Mock()
    app.extensions["model_sources"] = provider
    with app.app_context():
        assert ModelSources.for_instance(ProcessInstanceModel()).files is None
    provider.open.assert_not_called()


def test_provider_errors_propagate() -> None:
    app = Flask(__name__)
    app.extensions["model_sources"] = Mock(open=Mock(side_effect=RuntimeError("source unavailable")))
    with app.app_context(), pytest.raises(RuntimeError, match="source unavailable"):
        ModelSources.for_instance(ProcessInstanceModel(id=123))


def test_migration_policy_is_delegated() -> None:
    app = Flask(__name__)
    provider = Mock(spec=["assert_can_migrate"])
    instance = ProcessInstanceModel(id=123)
    app.extensions["model_sources"] = provider
    with app.app_context():
        ModelSources.assert_can_migrate(instance)
    provider.assert_can_migrate.assert_called_once_with(db.session, instance)
