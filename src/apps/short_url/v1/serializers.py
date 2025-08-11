import hashlib

from rest_framework import serializers

from apps.short_url.models import ShortUrl, ShortUrlVisit
from apps.short_url.v1.utils import generate_random_key, id_to_key
from base.enums.errors import (
    E005_HASHED_VALUE_ALREADY_EXISTS,
    E005_INVALID_OG_TAG_FORMAT,
)


class ShortUrlSerializer(serializers.ModelSerializer):
    """
    단축 URL 시리얼라이저:
    입력된 정보등을 이용해서 존재 여부 확인
    특별한 방식으로 중복되지 않는 고유한 값 생성
    항상 빠르고 안전하게 생성하고 관리
    """

    random_key = serializers.HiddenField(
        default=generate_random_key,
        help_text="랜덤 키",
    )
    hashed_value = serializers.HiddenField(
        default="",
        help_text="해시값",
    )
    short_key = serializers.CharField(
        read_only=True,
        help_text="단축 URL",
    )

    def validate_og_tag(self, value):
        # OG 태그는 JSON 형식
        if value and not isinstance(value, dict):
            raise serializers.ValidationError(E005_INVALID_OG_TAG_FORMAT)
        return value

    def validate(self, attrs):
        # hashed_value 값 생성
        concatenated = "".join(
            [
                attrs.get("ios_deep_link", ""),
                attrs.get("ios_fallback_url", ""),
                attrs.get("android_deep_link", ""),
                attrs.get("android_fallback_url", ""),
                attrs.get("default_fallback_url", ""),
            ]
        )

        # SHA-256 해시 생성
        # [Why]
        # Q. 왜 SHA-256 해시를 사용하는가?
        # A. SHA-256은 보안성이 높고, 해시 충돌 가능성이 낮기 때문
        #    또한, 해시값이 고유해야 하므로, 단축 URL 생성 시 중복 체크를 위해 사용
        hasher = hashlib.sha256()
        hasher.update(concatenated.encode("utf-8"))
        hashed_value = hasher.hexdigest()

        if ShortUrl.objects.filter(hashed_value=hashed_value).exists():
            raise serializers.ValidationError(E005_HASHED_VALUE_ALREADY_EXISTS)
        attrs["hashed_value"] = hashed_value
        return attrs

    def to_representation(self, instance):
        # ShortURL 의 Key 값 생성
        short_key = id_to_key(instance.id)
        random_key = instance.random_key
        # [Why]
        # Q. 왜 랜덤 키와 PK에 대한 인덱스를 사용하여 단축 URL을 생성하는가?
        # A. 랜덤 키는 고유성을 보장하고, PK는 데이터베이스에서의 유일성을 보장하기 때문
        #    두 값을 조합할 경우 언제나 고유한 단축 URL을 생성할 수 있음
        instance.short_key = f"{random_key[:2]}{short_key}{random_key[2:]}"
        return super().to_representation(instance)

    class Meta:
        model = ShortUrl
        fields = [
            "id",
            "short_key",
            "random_key",
            "ios_deep_link",
            "ios_fallback_url",
            "android_deep_link",
            "android_fallback_url",
            "default_fallback_url",
            "hashed_value",
            "og_tag",
        ]


class ShortUrlRedirectSerializer(serializers.ModelSerializer):
    """
    단축 URL 리다이렉트 시리얼라이저:
    숏링크에 해당하는 원본 링크로 리다이렉트
    방문 기록 저장
    """

    def save(self, **kwargs):
        # 요청 객체에서 필요한 정보 추출
        request = self.context.get("request")

        # IP 주소 추출
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # X-Forwarded-For가 있으면 첫 번째 IP(실제 클라이언트 IP)만 사용
            ip_address = x_forwarded_for.split(",")[0].strip()
        else:
            # 없으면 REMOTE_ADDR 사용
            ip_address = request.META.get("REMOTE_ADDR")

        # 추가 데이터 추출
        user_agent = request.META.get("HTTP_USER_AGENT")
        referrer = request.query_params.get("referrer")

        # 방문 기록 생성
        ShortUrlVisit.objects.create(
            short_url=self.instance,
            referrer=referrer,
            user_agent=user_agent,
            ip_address=ip_address,
        )

    class Meta:
        model = ShortUrl
        fields = [
            "id",
            "ios_deep_link",
            "ios_fallback_url",
            "android_deep_link",
            "android_fallback_url",
            "default_fallback_url",
            "hashed_value",
            "og_tag",
        ]
