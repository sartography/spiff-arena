"""Loads and sets up all database models for SQLAlchemy.

autoflake8 will remove these lines without the noqa comment

NOTE: make sure this file is ignored by reorder-python-imports since
some models need to be loaded before others for relationships and to
avoid circular imports
"""


from flask_bpmn.models.db import add_listeners

# must load these before UserModel and GroupModel for relationships
from spiffworkflow_backend.models.user_group_assignment import (
    UserGroupAssignmentModel,
)  # noqa: F401
from spiffworkflow_backend.models.principal import PrincipalModel  # noqa: F401


from spiffworkflow_backend.models.active_task import ActiveTaskModel  # noqa: F401
from spiffworkflow_backend.models.bpmn_process_id_lookup import (
    BpmnProcessIdLookup,
)  # noqa: F401
from spiffworkflow_backend.models.data_store import DataStoreModel  # noqa: F401
from spiffworkflow_backend.models.file import FileModel  # noqa: F401
from spiffworkflow_backend.models.message_correlation_property import (
    MessageCorrelationPropertyModel,
)  # noqa: F401
from spiffworkflow_backend.models.message_instance import (
    MessageInstanceModel,
)  # noqa: F401
from spiffworkflow_backend.models.message_model import MessageModel  # noqa: F401
from spiffworkflow_backend.models.message_triggerable_process_model import (
    MessageTriggerableProcessModel,
)  # noqa: F401
from spiffworkflow_backend.models.permission_assignment import (
    PermissionAssignmentModel,
)  # noqa: F401
from spiffworkflow_backend.models.permission_target import (
    PermissionTargetModel,
)  # noqa: F401
from spiffworkflow_backend.models.process_instance import (
    ProcessInstanceModel,
)  # noqa: F401
from spiffworkflow_backend.models.process_instance_report import (
    ProcessInstanceReportModel,
)  # noqa: F401
from spiffworkflow_backend.models.refresh_token import RefreshTokenModel  # noqa: F401
from spiffworkflow_backend.models.secret_model import SecretModel  # noqa: F401
from spiffworkflow_backend.models.spiff_logging import SpiffLoggingModel  # noqa: F401
from spiffworkflow_backend.models.task_event import TaskEventModel  # noqa: F401
from spiffworkflow_backend.models.user import UserModel  # noqa: F401
from spiffworkflow_backend.models.group import GroupModel  # noqa: F401

add_listeners()
