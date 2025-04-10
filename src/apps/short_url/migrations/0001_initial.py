# Generated by Django 5.1.7 on 2025-04-08 05:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ShortUrl",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("random_key", models.CharField(max_length=4, verbose_name="랜덤 키")),
                (
                    "ios_deep_link",
                    models.CharField(
                        blank=True, max_length=255, null=True, verbose_name="iOS 딥링크"
                    ),
                ),
                (
                    "ios_fallback_url",
                    models.URLField(blank=True, null=True, verbose_name="iOS 폴백 URL"),
                ),
                (
                    "android_deep_link",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="안드로이드 딥링크",
                    ),
                ),
                (
                    "android_fallback_url",
                    models.URLField(
                        blank=True, null=True, verbose_name="안드로이드 폴백 URL"
                    ),
                ),
                ("default_fallback_url", models.URLField(verbose_name="기본 폴백 URL")),
                (
                    "hashed_value",
                    models.CharField(
                        db_index=True, max_length=64, verbose_name="해시값"
                    ),
                ),
                (
                    "og_tag",
                    models.JSONField(blank=True, null=True, verbose_name="OG 태그"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="생성 일시"),
                ),
            ],
            options={
                "verbose_name": "단축 URL",
                "verbose_name_plural": "단축 URL",
                "db_table": "short_url",
            },
        ),
        migrations.CreateModel(
            name="ShortUrlVisit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "referrer",
                    models.CharField(
                        blank=True, max_length=255, null=True, verbose_name="레퍼러"
                    ),
                ),
                (
                    "user_agent",
                    models.TextField(
                        blank=True, null=True, verbose_name="사용자 에이전트"
                    ),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(
                        blank=True, null=True, verbose_name="IP 주소"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="생성 일시"),
                ),
                (
                    "short_url",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="short_url.shorturl",
                        verbose_name="단축 URL",
                    ),
                ),
            ],
            options={
                "verbose_name": "단축 URL 방문",
                "verbose_name_plural": "단축 URL 방문",
                "db_table": "short_url_visit",
            },
        ),
    ]
