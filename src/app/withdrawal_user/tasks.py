from celery import shared_task
from dateutil import relativedelta
from django.utils import timezone

from app.withdrawal_user.models import WithdrawalUser


@shared_task
def task_delete_withdrawal_user():
    WithdrawalUser.objects.filter(
        created_at__lte=timezone.now() - relativedelta.relativedelta(year=5)
    ).delete()
