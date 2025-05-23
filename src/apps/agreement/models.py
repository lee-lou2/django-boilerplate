from django.db import models

from apps.agreement.v1.tasks import task_send_re_agreement_notification
from apps.user.models import User


class AgreementType(models.IntegerChoices):
    """Agreement Type"""

    SERVICES = 1, "Terms of Service"
    PRIVACY = 2, "Privacy Policy"
    MARKETING = 3, "Marketing Agreement"


class Agreement(models.Model):
    """Agreement Information"""

    title = models.CharField(
        max_length=100,
        verbose_name="Agreement Title",
    )
    content = models.TextField(
        verbose_name="Agreement Content",
    )
    version = models.CharField(
        max_length=20,
        verbose_name="Agreement Version",
    )
    previous_version = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="next_versions",
        verbose_name="Previous Version",
        help_text="Refers to the previous version of the agreement before this revision.",
    )
    agreement_type = models.IntegerField(
        choices=AgreementType.choices,
        verbose_name="Agreement Type",
        help_text="1: Terms of Service, 2: Privacy Policy, 3: Marketing Agreement",
    )
    order = models.IntegerField(
        default=0,
        verbose_name="Agreement Order",
        help_text="The order in which it is displayed in the agreement list.",
    )
    is_required = models.BooleanField(
        default=False,
        verbose_name="Is Required",
        help_text="Indicates whether this is a mandatory agreement that the user must consent to.",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    def save(self, *args, **kwargs):
        # Cannot be modified
        # [Why]
        # Q. Why is modification prevented?
        # A. Agreements are legally binding documents, so any modifications require registration as a new version.
        if self.pk:
            raise ValueError("Agreements cannot be modified. Please register as a new version.")

        # Deactivate previous version if it exists and is active
        # [Why]
        # Q. Should the previous version be deactivated upon agreement revision?
        # A. Yes, upon agreement revision, the previous version should be deactivated
        #    to ensure the new agreement applies even if users consented to the previous version.
        if self.previous_version and self.is_active and self.previous_version.is_active:
            self.previous_version.is_active = False
            self.previous_version.save()

            # Schedule push/email notification for re-consent to users who agreed to the previous version
            # [Why]
            # Q. Why is re-consent required?
            # A. Agreements are legally binding, so revisions require users to re-consent.
            task_send_re_agreement_notification.apply_async(
                args=[self.previous_version, self],
            )
        super().save(*args, **kwargs)

    class Meta:
        db_table = "agreement"
        verbose_name = "Agreement Information"
        verbose_name_plural = "Agreement Information"


class UserAgreement(models.Model):
    """User Agreement Information"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_agreements",
        verbose_name="User",
    )
    agreement = models.ForeignKey(
        Agreement,
        on_delete=models.CASCADE,
        related_name="user_agreements",
        verbose_name="Agreement",
    )
    is_agreed = models.BooleanField(
        default=False,
        verbose_name="Is Agreed",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

    class Meta:
        db_table = "user_agreement"
        verbose_name = "User Agreement Information"
        verbose_name_plural = "User Agreement Information"
        unique_together = ["user", "agreement"]


class UserAgreementHistory(models.Model):
    """
    User Agreement History:
    A record of what changed when agreement information is modified is necessary.
    """

    user_agreement = models.ForeignKey(
        UserAgreement,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name="User Agreement Information",
    )
    data = models.JSONField(
        verbose_name="User agreement information before change",
        help_text="User agreement information before change (change date, consent status, agreement details, etc.)",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    class Meta:
        db_table = "user_agreement_history"
        verbose_name = "User Agreement History"
        verbose_name_plural = "User Agreement History"
