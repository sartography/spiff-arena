"""Loads and sets up all database models for SQLAlchemy.

autoflake8 will remove these lines without the noqa comment

NOTE: make sure this file is ignored by reorder-python-imports since
some models need to be loaded before others for relationships and to
avoid circular imports
"""

# unused imports are needed for SQLAlchemy to load the models
# ruff: noqa: F401

# we do not want to sort imports in this file, since the order matters
# ruff: noqa: I001

from spiffworkflow_backend.models.db import add_listeners

# must load these before UserModel and GroupModel for relationships
from spiffworkflow_backend.models.user_group_assignment import (
    UserGroupAssignmentModel,
)  # noqa: F401
from spiffworkflow_backend.models.principal import PrincipalModel  # noqa: F401


from spiffworkflow_backend.models.human_task import HumanTaskModel  # noqa: F401
from spiffworkflow_backend.models.cache_generation import (
    CacheGenerationModel,
)  # noqa: F401
from spiffworkflow_backend.models.reference_cache import (
    ReferenceCacheModel,
)  # noqa: F401
from spiffworkflow_backend.models.process_caller import (
    ProcessCallerCacheModel,
)  # noqa: F401
from spiffworkflow_backend.models.message_instance import (
    MessageInstanceModel,
)  # noqa: F401
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
from spiffworkflow_backend.models.user import UserModel  # noqa: F401
from spiffworkflow_backend.models.group import GroupModel  # noqa: F401
from spiffworkflow_backend.models.process_instance_metadata import (
    ProcessInstanceMetadataModel,
)  # noqa: F401
from spiffworkflow_backend.models.process_instance_file_data import (
    ProcessInstanceFileDataModel,
)  # noqa: F401

from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel  # noqa: F401
from spiffworkflow_backend.models.bpmn_process_definition import (
    BpmnProcessDefinitionModel,
)  # noqa: F401
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.task_definition import (
    TaskDefinitionModel,
)  # noqa: F401
from spiffworkflow_backend.models.json_data import JsonDataModel  # noqa: F401
from spiffworkflow_backend.models.bpmn_process_definition_relationship import (
    BpmnProcessDefinitionRelationshipModel,
)  # noqa: F401
from spiffworkflow_backend.models.process_instance_queue import (
    ProcessInstanceQueueModel,
)  # noqa: F401
from spiffworkflow_backend.models.active_user import (
    ActiveUserModel,
)  # noqa: F401
from spiffworkflow_backend.models.process_model_cycle import (
    ProcessModelCycleModel,
)  # noqa: F401
from spiffworkflow_backend.models.typeahead import (
    TypeaheadModel,
)  # noqa: F401
from spiffworkflow_backend.models.json_data_store import (
    JSONDataStoreModel,
)  # noqa: F401
from spiffworkflow_backend.models.kkv_data_store import (
    KKVDataStoreModel,
)  # noqa: F401
from spiffworkflow_backend.models.kkv_data_store_entry import (
    KKVDataStoreEntryModel,
)  # noqa: F401
from spiffworkflow_backend.models.task_draft_data import (
    TaskDraftDataModel,
)  # noqa: F401
from spiffworkflow_backend.models.configuration import (
    ConfigurationModel,
)  # noqa: F401
from spiffworkflow_backend.models.user_property import (
    UserPropertyModel,
)  # noqa: F401
from spiffworkflow_backend.models.service_account import (
    ServiceAccountModel,
)  # noqa: F401
from spiffworkflow_backend.models.message_model import (
    MessageModel,
    MessageCorrelationPropertyModel,
)  # noqa: F401
from spiffworkflow_backend.models.future_task import (
    FutureTaskModel,
)  # noqa: F401
from spiffworkflow_backend.models.feature_flag import (
    FeatureFlagModel,
)  # noqa: F401
from spiffworkflow_backend.models.process_caller_relationship import ProcessCallerRelationshipModel  # noqa: F401

add_listeners()
