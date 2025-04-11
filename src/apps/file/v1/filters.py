from django_filters import rest_framework as filters

from apps.file.models import File


class FileFilterSet(filters.FilterSet):
    """파일 필터셋"""

    content_type = filters.ModelChoiceFilter(
        field_name="content_type",
        lookup_expr="exact",
        required=True,
        label="컨텐츠 타입 (필수)",
    )

    class Meta:
        model = File
        fields = {
            "uuid": ["exact"],
            "object_id": ["exact"],
        }
