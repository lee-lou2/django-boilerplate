from celery import shared_task


@shared_task
def my_task(arg1, arg2):
    # Task logic here
    result = arg1 + arg2
    return result
