from spiffworkflow_backend import create_app

flask_app = create_app()
celery_app = flask_app.extensions["celery"]
# flask_app.app_context().push()
with flask_app.app_context():
    from spiffworkflow_backend.celery.task_one import task_one
    print(f"app.tasks: {celery_app.tasks.keys()}")
