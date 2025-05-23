import re

from better_profanity import profanity
from rest_framework import serializers

from apps.user.models import UserProfile, UserPreference
from common.enums.errors import (
    E008_NICKNAME_CONTAINS_FORBIDDEN_WORD,
    E008_INVALID_NICKNAME_LENGTH,
    E008_INVALID_NICKNAME_SPACING,
    E008_INVALID_NICKNAME_CONSECUTIVE_SPACES,
    E008_INVALID_NICKNAME_FORMAT,
    E008_NICKNAME_CONTAINS_PROFANITY,
)


class UserProfileSerializer(serializers.ModelSerializer):
    """
    User Profile Serializer:
    Nickname validation
    Profile registration
    """

    NICKNAME_ALLOWED_CHARS_REGEX = re.compile(
        r"^[a-zA-Z0-9가-힣\-_.+=^!\s"  # Basic characters + allowed special characters + space
        r"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
        r"\U0001F600-\U0001F64F"  # Emoticons
        r"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
        r"\u2600-\u26FF"  # Miscellaneous Symbols
        r"\u2700-\u27BF"  # Dingbats
        r"\uFE00-\uFE0F"  # Variation Selectors (for emoji styling)
        r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        r"]+$"
    )
    NICKNAME_MIN_LEN = 2
    NICKNAME_MAX_LEN = 30
    NICKNAME_FORBIDDEN_WORDS = {
        "admin",
        "administrator",
        "operator",  # "관리자", "운영자" translated
    }

    def validate_nickname(self, value):
        """
        Nickname validation
        1. Length check (2-30 characters)
        2. Leading/trailing space check
        3. Consecutive space check
        4. Allowed characters/symbols/emojis/spaces check (regex)
        5. Forbidden words check (admin, operator, etc.)
        6. Profanity check
        """
        # 1. Length check
        if not (self.NICKNAME_MIN_LEN <= len(value) <= self.NICKNAME_MAX_LEN):
            raise serializers.ValidationError(E008_INVALID_NICKNAME_LENGTH)

        # 2. Leading/trailing space check
        if value.startswith(" ") or value.endswith(" "):
            raise serializers.ValidationError(E008_INVALID_NICKNAME_SPACING)

        # 3. Consecutive space check
        if "  " in value:
            raise serializers.ValidationError(E008_INVALID_NICKNAME_CONSECUTIVE_SPACES)

        # 4. Allowed character combination check (regex)
        #    - Regex checks if the entire string consists only of allowed characters
        if not self.NICKNAME_ALLOWED_CHARS_REGEX.match(value):
            raise serializers.ValidationError(E008_INVALID_NICKNAME_FORMAT)

        # 5. Forbidden words check (case-insensitive)
        if value.lower() in self.NICKNAME_FORBIDDEN_WORDS:
            raise serializers.ValidationError(E008_NICKNAME_CONTAINS_FORBIDDEN_WORD)

        # 6. Profanity check
        #    - better_profanity might be English-centric, consider adding a Korean profanity library if needed
        if profanity.contains_profanity(value):
            raise serializers.ValidationError(E008_NICKNAME_CONTAINS_PROFANITY)

        return value  # Return the original value if all checks pass

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "nickname",
            "image",
        ]


class UserPreferenceSerializer(serializers.ModelSerializer):
    """
    User Preference Serializer:
    User preference settings
    To be used for future push notifications
    """

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        # TODO: Update subscription information for AWS SNS
        return instance

    class Meta:
        model = UserPreference
        fields = [
            "id",
            "user",
            "is_night_notification",
            "is_push_notification",
            "is_email_notification",
            "created_at",
        ]
