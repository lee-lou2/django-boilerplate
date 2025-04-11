from django_filters import rest_framework as filters

from apps.feed.models import Feed


class FeedFilterSet(filters.FilterSet):
    """피드 필터셋"""

    tag = filters.CharFilter(
        field_name="tags__name",
        lookup_expr="icontains",
        help_text="태그",
    )
    author = filters.UUIDFilter(
        field_name="user__uuid",
        lookup_expr="exact",
        help_text="작성자 UUID",
    )

    class Meta:
        model = Feed
        fields = {
            "published_at": ["gte", "lte"],
            "uuid": ["exact"],
            "title": ["icontains"],
        }


class FeedCommentFilterSet(filters.FilterSet):
    """피드 댓글 필터셋"""

    parent = filters.UUIDFilter(
        field_name="parent__uuid",
        lookup_expr="exact",
        help_text="부모 댓글 UUID",
    )
