from celery import Celery

def setup_celery() -> Celery:
    app = Celery('checker')
    app.config_from_object('celeryconfig')
    return app
