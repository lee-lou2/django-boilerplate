import hashlib

from django.contrib import admin

from .models import ShortUrl, ShortUrlVisit


@admin.register(ShortUrl)
class ShortUrlAdmin(admin.ModelAdmin):
    """단축 URL 어드민"""

    list_display = [
        "id",
        "random_key",
        "default_fallback_url",
        "ios_deep_link",
        "android_deep_link",
        "created_at",
    ]

    readonly_fields = [
        "random_key",
        "hashed_value",
        "created_at",
    ]

    search_fields = [
        "id",
        "random_key",
        "ios_deep_link",
        "android_deep_link",
        "default_fallback_url",
    ]

    list_filter = ["created_at"]

    fieldsets = (
        ("기본 정보", {"fields": ("random_key", "hashed_value", "created_at")}),
        (
            "URL 정보",
            {
                "fields": (
                    "default_fallback_url",
                    "ios_deep_link",
                    "ios_fallback_url",
                    "android_deep_link",
                    "android_fallback_url",
                )
            },
        ),
        ("OG 태그", {"fields": ("og_tag",)}),
    )

    def has_add_permission(self, request):
        """생성 권한 비활성화"""
        return False

    def save_model(self, request, obj, form, change):
        """모델 저장 시 hashed_value 자동 업데이트"""
        # 기존 해시값 저장
        old_hash = obj.hashed_value

        # 새 해시값 생성
        concatenated = "".join(
            [
                obj.ios_deep_link or "",
                obj.ios_fallback_url or "",
                obj.android_deep_link or "",
                obj.android_fallback_url or "",
                obj.default_fallback_url or "",
            ]
        )

        # SHA-256 해시 생성
        hasher = hashlib.sha256()
        hasher.update(concatenated.encode("utf-8"))
        new_hash = hasher.hexdigest()

        # 해시값이 변경되었는지 확인
        if new_hash != old_hash:
            # 같은 해시값을 가진 다른 객체가 있는지 확인
            # 현재 객체는 제외하고 검색
            if (
                ShortUrl.objects.exclude(id=obj.id)
                .filter(hashed_value=new_hash)
                .exists()
            ):
                # 중복된 해시값이 있으면 에러 발생
                self.message_user(
                    request,
                    f"저장할 수 없습니다: 같은 URL 조합을 가진 다른 단축 URL이 이미 존재합니다.",
                    level="error",
                )
                # 저장하지 않고 리턴
                return

            # 중복이 없으면 새 해시값으로 업데이트
            obj.hashed_value = new_hash

        # 모델 저장
        super().save_model(request, obj, form, change)


@admin.register(ShortUrlVisit)
class ShortUrlVisitAdmin(admin.ModelAdmin):
    """단축 URL 방문 어드민"""

    # 기존 코드와 동일
    list_display = [
        "id",
        "short_url",
        "ip_address",
        "referrer",
        "created_at",
    ]

    readonly_fields = [
        "short_url",
        "ip_address",
        "user_agent",
        "referrer",
        "created_at",
    ]

    search_fields = [
        "short_url__random_key",
        "ip_address",
        "referrer",
    ]

    list_filter = ["created_at"]

    def has_add_permission(self, request):
        """생성 권한 비활성화"""
        return False

    def has_change_permission(self, request, obj=None):
        """수정 권한 비활성화"""
        return False

    def has_delete_permission(self, request, obj=None):
        """삭제 권한 비활성화"""
        return False
