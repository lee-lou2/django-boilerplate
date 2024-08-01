from django.db import models


class BooleanChoices(models.TextChoices):
    Y = "Y", "Y"
    N = "N", "N"
