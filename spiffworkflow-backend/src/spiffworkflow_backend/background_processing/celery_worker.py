from spiffworkflow_backend import create_app
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task import (
    celery_task_process_instance_run,  # noqa: F401
)

the_flask_app = create_app()
setting_variable_to_make_celery_happy_no_idea_how_this_works = the_flask_app.celery_app
