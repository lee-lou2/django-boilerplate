import hashlib
import hmac
import logging
import math
import platform
import uuid

import requests
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import models
from django.utils import timezone
from firebase_admin import messaging

from app.common.models import BaseModel


class EmailLogStatus(models.TextChoices):
    READY = "R", "대기"
    SUCCESS = "S", "성공"
    FAILURE = "F", "실패"


class SmsLogStatus(models.TextChoices):
    READY = "R", "대기"
    SUCCESS = "S", "성공"
    FAILURE = "F", "실패"


class PushLogStatus(models.TextChoices):
    READY = "R", "대기"
    SUCCESS = "S", "성공"
    FAILURE = "F", "실패"


class EmailLog(BaseModel):
    to_set = models.JSONField(verbose_name="수신자", default=list)
    title = models.CharField(verbose_name="제목", max_length=128)
    content = models.TextField(verbose_name="내용")
    status = models.CharField(
        verbose_name="상태",
        max_length=1,
        choices=EmailLogStatus.choices,
        default=EmailLogStatus.READY,
    )
    fail_reason = models.TextField(verbose_name="실패사유", blank=True, default="")

    class Meta:
        db_table = "email_log"
        verbose_name = "이메일 로그"
        verbose_name_plural = verbose_name

    def send(self):
        subject = self.title
        message = self.content
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = self.to_set

        email = EmailMessage(subject, message, from_email, recipient_list)
        email.content_subtype = "html"
        try:
            email.send()
            self.status = EmailLogStatus.SUCCESS
        except Exception as e:
            logging.error(f"EmailLog.send error: {e}")
            self.status = EmailLogStatus.FAILURE
        self.save()


class PushLog(BaseModel):
    to_set = models.ManyToManyField("device.Device", verbose_name="수신자")
    title = models.CharField(verbose_name="제목", max_length=128)
    content = models.TextField(verbose_name="내용")
    status = models.CharField(
        verbose_name="상태",
        max_length=1,
        choices=PushLogStatus.choices,
        default=PushLogStatus.READY,
    )
    fail_reason = models.TextField(verbose_name="실패사유", blank=True, default="")

    class Meta:
        db_table = "push_log"
        verbose_name = "푸시 로그"
        verbose_name_plural = verbose_name

    def send(self):
        device_set = self.to_set.all()
        failed_device_set = []
        for i in range(math.ceil(len(device_set) / 500)):
            message = messaging.MulticastMessage(
                tokens=[device.token for device in device_set[500 * i : 500 * (i + 1)]],
                notification=messaging.Notification(
                    title=self.title,
                    body=self.content,
                ),
            )
            response = messaging.send_multicast(message)
            if response.failure_count > 0:
                responses = response.responses
                for idx, resp in enumerate(responses):
                    if not resp.success:
                        failed_device_set.append(device_set[idx])
        self.to_set.model.objects.filter(
            id__in=[device.id for device in failed_device_set]
        ).delete()


class SmsLog(BaseModel):
    to_set = models.JSONField(verbose_name="수신자", default=list)
    title = models.CharField(verbose_name="제목", max_length=128)
    content = models.TextField(verbose_name="내용")
    status = models.CharField(
        verbose_name="상태",
        max_length=1,
        choices=SmsLogStatus.choices,
        default=SmsLogStatus.READY,
    )
    fail_reason = models.TextField(verbose_name="실패사유", blank=True, default="")

    class Meta:
        db_table = "sms_log"
        verbose_name = "문자 로그"
        verbose_name_plural = verbose_name

    def send(self):
        date = timezone.now().isoformat()
        salt = str(uuid.uuid1().hex)
        combined_string = date + salt

        headers = {
            "Authorization": "HMAC-SHA256 ApiKey="
            + settings.COOLSMS_API_KEY
            + ", Date="
            + date
            + ", salt="
            + salt
            + ", signature="
            + hmac.new(
                settings.COOLSMS_API_SECRET.encode(),
                combined_string.encode(),
                hashlib.sha256,
            ).hexdigest(),
            "Content-Type": "application/json; charset=utf-8",
        }
        data = {
            "agent": {
                "sdkVersion": "python/4.2.0",
                "osPlatform": platform.platform() + " | " + platform.python_version(),
            },
            "messages": [
                {
                    "from": settings.COOLSMS_FROM_PHONE,
                    "to": to,
                    "text": self.content,
                }
                for to in self.to_set
            ],
        }
        response = requests.request(
            method="post",
            url="https://api.coolsms.co.kr/messages/v4/send-many",
            headers=headers,
            json=data,
        )
        if response.ok:
            self.status = SmsLogStatus.SUCCESS
        else:
            self.status = SmsLogStatus.FAILURE
            # self.fail_reason
        self.save()
