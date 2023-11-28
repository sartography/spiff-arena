from spiffworkflow_backend import create_app
from spiffworkflow_backend.services.process_instance_lock_service import ProcessInstanceLockService

the_flask_app = create_app()
setting_variable_to_make_celery_happy_no_idea_how_this_works = the_flask_app.celery_app
with the_flask_app.app_context():
    ProcessInstanceLockService.set_thread_local_locking_context("celery:worker")
