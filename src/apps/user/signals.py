from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from apps.user.models import User


@receiver(user_logged_in, sender=User)
def post_login(sender, request, user, **kwargs):
    """로그인 시 처리"""

    pass
