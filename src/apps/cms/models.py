from django.db import models
from uuid_extensions import uuid7


class Notice(models.Model):
    """공지사항"""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid7,
        editable=False,
        verbose_name="UUID",
    )
    author = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        verbose_name="작성자",
        help_text="공지 작성자",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="제목",
        help_text="제목",
    )
    content = models.TextField(
        verbose_name="내용",
        help_text="내용",
    )
    published_at = models.DateTimeField(
        verbose_name="발행 일시",
        help_text="공지 발행 일시",
        db_index=True,
    )
    # 표시 기간
    start_at = models.DateTimeField(
        verbose_name="시작 일시",
        help_text="공지 시작 일시",
    )
    end_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="종료 일시",
        help_text="공지 종료 일시",
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name="발행 여부",
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
        db_table = "notice"
        verbose_name = "공지사항"
        verbose_name_plural = "공지사항"


class Event(models.Model):
    """이벤트"""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid7,
        editable=False,
        verbose_name="UUID",
    )
    author = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        verbose_name="작성자",
        help_text="이벤트 작성자",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="제목",
        help_text="제목",
    )
    content = models.TextField(
        verbose_name="내용",
        help_text="내용",
    )
    # 표시 기간
    start_at = models.DateTimeField(
        verbose_name="시작 일시",
        help_text="이벤트 시작 일시",
    )
    end_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="종료 일시",
        help_text="이벤트 종료 일시",
    )
    # 이벤트 기간
    event_start_at = models.DateTimeField(
        verbose_name="이벤트 시작 일시",
        help_text="이벤트 시작 일시",
    )
    event_end_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="이벤트 종료 일시",
        help_text="이벤트 종료 일시",
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name="발행 여부",
    )
    published_at = models.DateTimeField(
        verbose_name="발행 일시",
        help_text="이벤트 발행 일시",
        db_index=True,
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
        db_table = "event"
        verbose_name = "이벤트"
        verbose_name_plural = "이벤트"


class FaqCategory(models.Model):
    """FAQ 카테고리"""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid7,
        editable=False,
        verbose_name="UUID",
    )
    name = models.CharField(
        max_length=255,
        verbose_name="카테고리 이름",
        help_text="카테고리 이름",
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
        db_table = "faq_category"
        verbose_name = "FAQ 카테고리"
        verbose_name_plural = "FAQ 카테고리"


class Faq(models.Model):
    """FAQ"""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid7,
        editable=False,
        verbose_name="UUID",
    )
    author = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        verbose_name="작성자",
        help_text="FAQ 작성자",
    )
    category = models.ForeignKey(
        FaqCategory,
        on_delete=models.CASCADE,
        verbose_name="카테고리",
        help_text="FAQ 카테고리",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="제목",
        help_text="제목",
    )
    content = models.TextField(
        verbose_name="내용",
        help_text="내용",
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name="발행 여부",
    )
    published_at = models.DateTimeField(
        verbose_name="발행 일시",
        help_text="FAQ 발행 일시",
        db_index=True,
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
        db_table = "faq"
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"
