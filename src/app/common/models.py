from django.db import models


class BaseModelMixin(models.Model):
    created_at = models.DateTimeField(verbose_name="생성일시", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="수정일시", auto_now=True)

    class Meta:
        abstract = True


BaseModel = BaseModelMixin
