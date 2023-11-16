from spiffworkflow_backend import create_app

app = create_app()
with app.app_context():
    from spiffworkflow_backend.celery.task_one import task_one
    task_one.delay()
