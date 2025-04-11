from django.contrib import admin
from django.utils.html import format_html

from .models import Agreement, UserAgreement


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    """
    약관 정보 Admin 설정
    - 생성: 가능
    - 수정: 불가능 (UI상 readonly 처리 + 모델 save 메서드에서 방지)
    - 삭제: 불가능
    """

    list_display = (
        "title",
        "version",
        "get_agreement_type_display",
        "order",
        "is_required",
        "is_active",
        "previous_version_link",
        "created_at",
    )
    list_filter = ("agreement_type", "is_required", "is_active")
    search_fields = ("title", "version", "content")
    ordering = ("-created_at",)  # 최신순 정렬

    fields = (
        "title",
        "content",
        "version",
        "previous_version",
        "agreement_type",
        "order",
        "is_required",
        "is_active",
    )

    def get_readonly_fields(self, request, obj=None):
        """
        객체가 이미 존재하면 (수정 시도 시) 모든 필드를 읽기 전용으로 만듭니다.
        """
        if obj:
            # 모든 모델 필드를 읽기 전용으로 반환
            return [field.name for field in self.opts.model._meta.fields]
        return []

    def has_change_permission(self, request, obj=None):
        """
        수정 권한 제어 (UI상 버튼 비활성화 등). get_readonly_fields와 함께 사용.
        모델 레벨에서도 막고 있지만, UI 상에서도 명확히 하기 위함.
        """
        if obj:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        삭제 권한을 비활성화합니다.
        """
        return False

    def get_agreement_type_display(self, obj):
        """
        IntegerField + Choices 필드의 display 값을 list_display에 보여줍니다.
        """
        return obj.get_agreement_type_display()

    get_agreement_type_display.short_description = "약관 타입"

    def previous_version_link(self, obj):
        """
        이전 버전 약관 관리자 페이지로 바로 이동하는 링크 (선택 사항)
        """
        if obj.previous_version:
            link = f"/admin/{obj._meta.app_label}/{obj._meta.model_name}/{obj.previous_version.pk}/change/"
            return format_html(
                '<a href="{}">{} (v{})</a>',
                link,
                obj.previous_version.title,
                obj.previous_version.version,
            )
        return "-"

    previous_version_link.short_description = "이전 버전"


@admin.register(UserAgreement)
class UserAgreementAdmin(admin.ModelAdmin):
    """
    사용자 약관 동의 정보 Admin 설정
    - 생성: 불가능
    - 수정: 불가능
    - 삭제: 불가능
    - 조회: 가능 (사용자, 약관 타입 등으로 필터링 가능)
    """

    list_display = (
        "user",
        "get_agreement_info",
        "is_agreed",
        "created_at",
    )
    list_filter = ("is_agreed", "agreement__agreement_type")
    search_fields = (
        "user__username",
        "agreement__title",
        "agreement__version",
    )
    ordering = ("-created_at",)

    readonly_fields = ("user", "agreement", "is_agreed", "created_at")

    def has_add_permission(self, request):
        """
        생성 권한을 비활성화합니다.
        """
        return False

    def has_change_permission(self, request, obj=None):
        """
        수정 권한을 비활성화합니다. (readonly_fields 설정으로도 충분하지만 명시적으로 추가)
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        삭제 권한을 비활성화합니다.
        """
        return False

    def get_agreement_info(self, obj):
        """
        연결된 약관의 제목과 버전을 함께 보여줍니다.
        """
        if obj.agreement:
            return f"{obj.agreement.title} (v{obj.agreement.version})"
        return "-"

    get_agreement_info.short_description = "동의한 약관"
