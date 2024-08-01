from app.common.models import BaseModel
from app.user.models import BaseUser, User


class WithdrawalUser(BaseUser):
    is_active = None
    is_staff = None
    is_superuser = None
    password = None
    last_login = None
    groups = None
    user_permissions = None

    class Meta:
        db_table = "withdrawal_user"
        verbose_name = "탈퇴한 유저"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
