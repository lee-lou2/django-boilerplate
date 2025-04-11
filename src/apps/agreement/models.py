from django.db import models

from apps.agreement.v1.tasks import task_send_re_agreement_notification
from apps.user.models import User


class AgreementType(models.IntegerChoices):
    """약관 타입"""

    SERVICES = 1, "서비스 약관"
    PRIVACY = 2, "개인정보 처리 방침"
    MARKETING = 3, "마케팅 약관"


class Agreement(models.Model):
    """약관 정보"""

    title = models.CharField(
        max_length=100,
        verbose_name="약관 제목",
    )
    content = models.TextField(
        verbose_name="약관 내용",
    )
    version = models.CharField(
        max_length=20,
        verbose_name="약관 버전",
    )
    previous_version = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="next_versions",
        verbose_name="이전 버전",
        help_text="이 약관 개정 전의 이전 버전 약관을 참조합니다.",
    )
    agreement_type = models.IntegerField(
        choices=AgreementType.choices,
        verbose_name="약관 타입",
        help_text="1: 서비스 약관, 2: 개인정보 처리 방침, 3: 마케팅 약관",
    )
    order = models.IntegerField(
        default=0,
        verbose_name="약관 순서",
        help_text="약관 목록에서 표시되는 순서입니다.",
    )
    is_required = models.BooleanField(
        default=False,
        verbose_name="필수 동의 여부",
        help_text="사용자가 동의해야 하는 필수 약관인지 여부를 나타냅니다.",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="활성화 여부",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )

    def save(self, *args, **kwargs):
        # 수정 불가
        # [Why]
        # Q. 수정을 막는 이유는?
        # A. 약관은 법적 효력이 있는 문서이기 때문에, 수정 시에는 새로운 버전으로 등록해야 합니다.
        if self.pk:
            raise ValueError("약관은 수정할 수 없습니다. 새로운 버전으로 등록하세요.")

        # 이전 버전이 존재하고 활성화된 경우 비활성화
        # [Why]
        # Q. 약관 개정 시 이전 버전은 비활성화해야 하는가?
        # A. 예, 약관 개정 시 이전 버전은 비활성화해야함
        #    사용자가 이전 버전의 약관에 동의한 경우에도, 새로운 약관이 적용되도록 하기 위함
        if self.previous_version and self.is_active and self.previous_version.is_active:
            self.previous_version.is_active = False
            self.previous_version.save()

            # 이미 해당 예전 약관을 동의한 사람들에게 재동의 요청 푸시/이메일 발송 예약
            # [Why]
            # Q. 왜 재동의 요청을 해야 하는가?
            # A. 약관은 법적 효력이 있는 문서이기 때문에, 개정 시에는 사용자에게 재동의 요청을 해야함
            task_send_re_agreement_notification.apply_async(
                args=[self.previous_version, self],
            )
        super().save(*args, **kwargs)

    class Meta:
        db_table = "agreement"
        verbose_name = "약관 정보"
        verbose_name_plural = "약관 정보"


class UserAgreement(models.Model):
    """사용자 약관 동의 정보"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_agreements",
        verbose_name="사용자",
    )
    agreement = models.ForeignKey(
        Agreement,
        on_delete=models.CASCADE,
        related_name="user_agreements",
        verbose_name="약관",
    )
    is_agreed = models.BooleanField(
        default=False,
        verbose_name="동의 여부",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정 일시",
    )

    class Meta:
        db_table = "user_agreement"
        verbose_name = "사용자 약관 동의 정보"
        verbose_name_plural = "사용자 약관 동의 정보"
        unique_together = ["user", "agreement"]


class UserAgreementHistory(models.Model):
    """
    사용자 약관 동의 이력:
    약관 정보가 변경될 경우 어떤 값이 어떻게 변경되었는지에 대한 기록 필요
    """

    user_agreement = models.ForeignKey(
        UserAgreement,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name="사용자 약관 동의 정보",
    )
    data = models.JSONField(
        verbose_name="변경 전 사용자 약관 동의 정보",
        help_text="변경 전 사용자 약관 동의 정보(변경 일시, 동의 여부, 약관 정보 등)",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시",
    )

    class Meta:
        db_table = "user_agreement_history"
        verbose_name = "사용자 약관 동의 이력"
        verbose_name_plural = "사용자 약관 동의 이력"
