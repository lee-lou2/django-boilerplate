import re

from django.conf import settings
from django.core.cache import caches
from rest_framework.exceptions import ValidationError

from app.taboo_word.models import TabooWord


class TabooWordMixin:
    TABOO_WORDS_CACHE_KEY = "taboo_words"
    TABOO_WORD_REGEX = None

    @classmethod
    def get_taboo_words_regex(cls):
        if cls.TABOO_WORD_REGEX is None:
            taboo_words = caches["default"].get(
                cls.TABOO_WORDS_CACHE_KEY, version=settings.CACHE_VERSION
            )
            if not taboo_words:
                taboo_words = TabooWord.objects.values_list("dirty_word", flat=True)
                caches["default"].set(
                    cls.TABOO_WORDS_CACHE_KEY,
                    taboo_words,
                    timeout=3600,
                    version=settings.CACHE_VERSION,
                )
            cls.TABOO_WORD_REGEX = re.compile(
                "|".join(map(re.escape, taboo_words)), re.IGNORECASE
            )
        return cls.TABOO_WORD_REGEX

    def clean_field_with_taboo_words(self, field_name, field_value):
        taboo_regex = self.get_taboo_words_regex()
        if taboo_regex.search(field_value):
            raise ValidationError({field_name: ["본문에 금칙어가 존재합니다."]})
