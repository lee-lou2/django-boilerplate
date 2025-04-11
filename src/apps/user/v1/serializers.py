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
    사용자 프로필 시리얼라이저:
    닉네임 유효성 검사
    프로필 등록
    """

    NICKNAME_ALLOWED_CHARS_REGEX = re.compile(
        r"^[a-zA-Z0-9가-힣\-_.+=^!\s"  # 기본 문자 + 허용 특수문자 + 공백
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
        "관리자",
        "운영자",
        "어드민",
    }

    def validate_nickname(self, value):
        """
        닉네임 유효성 검사
        1. 길이 검사 (2~30자)
        2. 시작/끝 공백 검사
        3. 연속 공백 검사
        4. 허용된 문자/기호/이모티콘/공백 검사 (정규식)
        5. 금지된 단어 검사 (admin, 관리자 등)
        6. 비속어 검사
        """
        # 1. 길이 검사
        if not (self.NICKNAME_MIN_LEN <= len(value) <= self.NICKNAME_MAX_LEN):
            raise serializers.ValidationError(E008_INVALID_NICKNAME_LENGTH)

        # 2. 시작/끝 공백 검사
        if value.startswith(" ") or value.endswith(" "):
            raise serializers.ValidationError(E008_INVALID_NICKNAME_SPACING)

        # 3. 연속 공백 검사
        if "  " in value:
            raise serializers.ValidationError(E008_INVALID_NICKNAME_CONSECUTIVE_SPACES)

        # 4. 허용된 문자 조합 검사 (정규식)
        #    - 정규식은 전체 문자열이 허용된 문자들로만 구성되었는지 확인
        if not self.NICKNAME_ALLOWED_CHARS_REGEX.match(value):
            raise serializers.ValidationError(E008_INVALID_NICKNAME_FORMAT)

        # 5. 금지된 단어 검사 (대소문자 무시)
        if value.lower() in self.NICKNAME_FORBIDDEN_WORDS:
            raise serializers.ValidationError(E008_NICKNAME_CONTAINS_FORBIDDEN_WORD)

        # 6. 비속어 검사
        #    - better_profanity 는 영어 중심일 수 있으므로, 필요시 한국어 비속어 라이브러리 추가 고려
        if profanity.contains_profanity(value):
            raise serializers.ValidationError(E008_NICKNAME_CONTAINS_PROFANITY)

        return value  # 모든 검사를 통과하면 원래 값 반환

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "nickname",
            "image",
        ]


class UserPreferenceSerializer(serializers.ModelSerializer):
    """
    사용자 선호도 시리얼라이저:
    사용자 선호도 설정
    추후 푸시 발송 시 사용
    """

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        # TODO: AWS SNS 의 구독 정보 업데이트
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
