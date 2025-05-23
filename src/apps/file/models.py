from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from uuid_extensions import uuid7


class FileStatus(models.IntegerChoices):
    """File Status"""

    READY = 1, "Ready"
    GENERATED = 2, "Generated"
    SUCCESS_UPLOAD = 3, "Upload Successful"
    FAIL_UPLOAD = 4, "Upload Failed"
    DELETE = 5, "Deleted"


class FileContentType(models.IntegerChoices):
    """File Content Type"""

    OTHER = 1, "Other"
    QNA = 2, "QnA"


class File(models.Model):
    """File"""

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid7,
        editable=False,
        verbose_name="File ID used for storage",
    )
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="files",
    )
    file_name = models.CharField(
        max_length=100,
        verbose_name="Actual file name",
    )
    extension = models.CharField(
        max_length=10,
        verbose_name="File extension",
    )
    file_size = models.IntegerField(
        default=0,
        verbose_name="File size",
    )
    object_key = models.TextField(
        verbose_name="File URL",
        null=True,
        blank=True,
    )
    # [Why]
    # Q. Why use ContentType and ObjectId?
    # A. Files are often linked to specific objects, which can be of various models.
    #    Therefore, GenericForeignKey is used to link to various models.
    # Q. Why nullable?
    # A. A file may not be linked to a specific object.
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        related_name="files",
        null=True,
        verbose_name="Content Type",
    )
    object_id = models.CharField(
        max_length=36,
        null=True,
        verbose_name="Content ID",
    )
    content_object = GenericForeignKey("content_type", "object_id")
    status = models.PositiveSmallIntegerField(
        choices=FileStatus,
        verbose_name="File Status",
        default=FileStatus.READY,
    )
    expire_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Expiration At",
        db_index=True,
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
        db_table = "file"
        verbose_name = "File"
        verbose_name_plural = "Files"
        # [Why]
        # Q. Why set ContentType and ObjectId as a composite key?
        # A. Because these two values are always used together, and this combination ensures uniqueness.
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]


# [Why]
# Q. Why create the FileDownloadHistory model?
# A. To store file download history.
# Q. What information is stored?
# A. The user who requested the download, the reason for download, the downloaded file, and the creation timestamp.
class FileDownloadHistory(models.Model):
    """File Download History"""

    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="file_download_history",
    )
    reason = models.CharField(
        max_length=100,
        verbose_name="Download Reason",
        null=True,
        blank=True,
    )
    file = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        related_name="download_history",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    class Meta:
        db_table = "file_download_history"
        verbose_name = "File Download History"
        verbose_name_plural = "File Download Histories"
