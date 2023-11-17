from spiffworkflow_backend import create_app

flask_app = create_app()
celery_app = flask_app.celery_app

with flask_app.app_context():
    import spiffworkflow_backend.celery_tasks
    print(f"app.tasks: {celery_app.tasks.keys()}")
