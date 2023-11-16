# from flask import current_app
from celery import shared_task

# @current_app.celery_app.task
@shared_task(ignore_result=False)
def task_one() -> int:
    return 1 + 2
