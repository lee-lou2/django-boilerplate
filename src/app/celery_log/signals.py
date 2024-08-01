import json

from celery.signals import task_failure, task_prerun, task_success

from app.celery_log.models import CeleryLog, CeleryLogStatus


@task_prerun.connect
def task_celery_prerun(sender=None, **kwargs):
    if not sender:
        return

    CeleryLog.objects.create(
        task_id=kwargs["task_id"],
        name=sender.name,
        status=CeleryLogStatus.PENDING,
        args=json.dumps(kwargs.get("args", [])),
        kwargs=json.dumps(kwargs.get("kwargs", {})),
    )


@task_success.connect
def task_celery_success(sender=None, result=None, **kwargs):
    if not sender:
        return

    CeleryLog.objects.filter(task_id=sender.request.id).update(
        status=CeleryLogStatus.SUCCESS, result=json.dumps(result)
    )


@task_failure.connect
def task_celery_failure(sender=None, **kwargs):
    if not sender:
        return

    CeleryLog.objects.filter(task_id=kwargs["task_id"]).update(
        status=CeleryLogStatus.FAILURE,
        message=str(kwargs.get("einfo").exception),
    )
