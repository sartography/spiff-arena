import time

from flask import current_app

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


def load_acceptance_test_fixtures() -> list[ProcessInstanceModel]:
    current_app.logger.debug("load_acceptance_test_fixtures() start")
    test_process_model_id = "misc/acceptance-tests-group-one/acceptance-tests-model-1"
    user = BaseTest.find_or_create_user()
    statuses = ProcessInstanceStatus.list()
    current_time = round(time.time())

    # as of 2022-06-24
    # not_started - 1 hour ago
    # user_input_required - 2 hours ago
    # waiting - 3 hourse ago
    # complete - 4 hours ago
    # error - 5 hours ago
    # suspended - 6 hours ago
    process_instances = []
    for i in range(len(statuses)):
        process_instance = ProcessInstanceService.create_process_instance_from_process_model_identifier(
            test_process_model_id, user
        )
        process_instance.status = statuses[i]
        process_instance.start_in_seconds = current_time - (3600 * i)
        process_instance.end_in_seconds = current_time - (3600 * i - 20)
        db.session.add(process_instance)
        process_instances.append(process_instance)

    db.session.commit()
    current_app.logger.debug("load_acceptance_test_fixtures() end")
    return process_instances
