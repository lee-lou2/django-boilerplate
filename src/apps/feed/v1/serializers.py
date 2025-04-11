from html import escape

from django.db import transaction, IntegrityError
from rest_framework import serializers

from apps.feed.models import (
    Feed,
    FeedComment,
    FeedTag,
    FeedLike,
    FeedReport,
    FeedReportReason,
    FeedCommentLike,
    FeedCommentReport,
)
from apps.feed.v1.fields import CurrentFeedDefault
from apps.user.models import UserProfile
from common.enums.errors import (
    E006_FEED_ALREADY_REPORTED,
    E006_COMMENT_ALREADY_REPORTED,
    E006_FEED_NOT_FOUND,
    E006_CANNOT_CHANGE_PARENT_COMMENT,
    E006_PARENT_COMMENT_NOT_FOUND,
)


class AuthorSerializer(serializers.ModelSerializer):
    """
    작성자 시리얼라이저:
    작성자의 닉네임과 이미지, UUID 조회
    """

    uuid = serializers.UUIDField(source="user.uuid", help_text="UUID")

    class Meta:
        model = UserProfile
        fields = ["uuid", "nickname", "image"]


class FeedTagSerializer(serializers.ModelSerializer):
    """
    피드 태그 시리얼라이저:
    피드에 등록된 태그 정보 조회
    """

    class Meta:
        model = FeedTag
        fields = ["id", "name"]


class FeedBestCommentSerializer(serializers.ModelSerializer):
    """
    피드 베스트 댓글 시리얼라이저:
    피드 베스트 댓글 정보 조회
    """

    author = AuthorSerializer(source="user.profile", help_text="작성자")

    class Meta:
        model = FeedComment
        fields = [
            "uuid",
            "author",
            "content",
            "likes_count",
            "reported_count",
            "reply_count",
            "is_deleted",
            "created_at",
            "updated_at",
        ]


class FeedSerializer(serializers.ModelSerializer):
    """
    피드 시리얼라이저:
    피드 생성, 수정, 삭제
    escape 를 이용해서 저장 시 XSS 방지
    태그는 별도의 테이블이므로 따로 저장
    """

    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(), help_text="사용자"
    )
    tags = FeedTagSerializer(many=True, help_text="태그 목록")

    def validate_title(self, attr):
        """제목 유효성 검사"""
        # XSS 예방을 위해 escaping
        return escape(attr, quote=False)

    def validate_content(self, attr):
        """내용 유효성 검사"""
        # XSS 예방을 위해 escaping
        return escape(attr, quote=False)

    def create(self, validated_data):
        tags = validated_data.pop("tags")
        feed = Feed.objects.create(**validated_data)
        # 태그 생성
        for tag in tags:
            tag_obj, _ = FeedTag.objects.get_or_create(name=tag.get("name"))
            feed.tags.add(tag_obj)
        return feed

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags")
        instance = super().update(instance, validated_data)
        # 태그 업데이트
        instance.tags.clear()
        for tag in tags:
            tag_obj, _ = FeedTag.objects.get_or_create(name=tag.get("name"))
            instance.tags.add(tag_obj)
        return instance

    class Meta:
        model = Feed
        fields = [
            "uuid",
            "user",
            "title",
            "content",
            "image",
            "likes_count",
            "comments_count",
            "reported_count",
            "tags",
            "published_at",
        ]
        read_only_fields = [
            "uuid",
            "likes_count",
            "comments_count",
            "reported_count",
        ]


class FeedListSerializer(serializers.ModelSerializer):
    """
    피드 리스트 시리얼라이저:
    피드 목록 조회
    좋아요 1개 이상, 상위 댓글 중 베스트 댓글 조회
    """

    author = AuthorSerializer(source="user.profile", help_text="작성자")
    is_like = serializers.BooleanField(help_text="좋아요 여부", default=False)
    is_reported = serializers.BooleanField(help_text="신고 여부", default=False)
    best_comment = serializers.SerializerMethodField(help_text="베스트 댓글")

    def get_best_comment(self, instance):
        """베스트 댓글 조회"""
        instance = (
            instance.feed_comments.select_related("user__profile")
            .filter(
                is_displayed=True, parent__isnull=True, likes_count__gt=0
            )  # 표시 중인 댓글, 부모 댓글, 좋아요 수 1 이상
            .order_by("-likes_count")  # 좋아요 많은 순
            .first()
        )
        serializer = FeedBestCommentSerializer(instance=instance) if instance else None
        return serializer.data if instance else None

    class Meta:
        model = Feed
        fields = [
            "uuid",
            "author",
            "title",
            "content",
            "best_comment",
            "likes_count",
            "comments_count",
            "reported_count",
            "is_like",
            "is_reported",
            "is_displayed",
            "published_at",
        ]


class FeedRetrieveSerializer(FeedListSerializer):
    """
    피드 상세 시리얼라이저:
    피드 기본 리스트 조회에 포함된 정보 외 태그 등의 추가 정보 조회
    """

    tags = FeedTagSerializer(many=True, help_text="태그 목록")

    class Meta:
        model = Feed
        fields = [
            "uuid",
            "author",
            "title",
            "content",
            "image",
            "tags",
            "likes_count",
            "comments_count",
            "reported_count",
            "is_like",
            "is_reported",
            "is_displayed",
            "published_at",
        ]


class FeedLikeSerializer(serializers.ModelSerializer):
    """
    피드 좋아요 시리얼라이저:
    좋아요 및 좋아요 취소
    """

    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(), help_text="사용자"
    )
    is_like = serializers.BooleanField(help_text="좋아요 여부", required=True)

    @transaction.atomic
    def update(self, instance, validated_data):
        is_like = validated_data.get("is_like")
        if is_like:
            _, is_create = FeedLike.objects.get_or_create(
                feed=instance, user=validated_data["user"]
            )
            instance.likes_count += 1 if is_create else 0
        else:
            FeedLike.objects.filter(feed=instance, user=validated_data["user"]).delete()
            instance.likes_count -= 1 if instance.likes_count > 0 else 0
        instance.save()
        return validated_data

    class Meta:
        model = Feed
        fields = [
            "user",
            "is_like",
        ]


class FeedReportSerializer(serializers.ModelSerializer):
    """
    피드 신고 시리얼라이저:
    피드 신고
    """

    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(), help_text="사용자"
    )
    report_reason = serializers.ChoiceField(
        choices=FeedReportReason, help_text="신고 사유"
    )
    content = serializers.CharField(
        help_text="내용", required=False, allow_blank=True, allow_null=True
    )

    @transaction.atomic
    def update(self, instance, validated_data):
        # 신고 생성
        try:
            FeedReport.objects.create(feed=instance, **validated_data)
        except IntegrityError:
            raise serializers.ValidationError(E006_FEED_ALREADY_REPORTED)
        # 신고 수 증가
        instance.reported_count += 1
        instance.save()
        return validated_data

    class Meta:
        model = Feed
        fields = [
            "user",
            "report_reason",
            "content",
        ]


class FeedCommentSerializer(serializers.ModelSerializer):
    """
    피드 댓글 시리얼라이저:
    피드 댓글 생성, 수정, 삭제
    """

    feed = serializers.HiddenField(default=CurrentFeedDefault(), help_text="피드 UUID")
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(), help_text="사용자"
    )

    def validate_feed(self, attr):
        """피드 유효성 검사"""
        feed = Feed.objects.filter(uuid=attr).first()
        if not feed:
            raise serializers.ValidationError(E006_FEED_NOT_FOUND)
        return feed

    def validate_parent(self, attr):
        """부모 댓글 유효성 검사"""
        if (
            attr
            and hasattr(self, "instance")
            and self.instance
            and self.instance.parent
            and self.instance.parent_id != attr
        ):
            raise serializers.ValidationError(E006_CANNOT_CHANGE_PARENT_COMMENT)
        if attr and not FeedComment.objects.filter(uuid=attr.uuid).exists():
            raise serializers.ValidationError(E006_PARENT_COMMENT_NOT_FOUND)
        return attr

    def validate_content(self, attr):
        """내용 유효성 검사"""
        # XSS 예방을 위해 escaping
        return escape(attr, quote=False)

    def create(self, validated_data):
        instance = super().create(validated_data)
        # 피드의 댓글 수 증가
        if instance.parent is None:
            instance.feed.comments_count += 1
            instance.feed.save()
        else:
            # 부모 댓글의 답글 수 증가
            instance.parent.reply_count += 1
            instance.parent.save()
        return instance

    class Meta:
        model = FeedComment
        fields = [
            "uuid",
            "user",
            "feed",
            "parent",
            "content",
            "likes_count",
            "reported_count",
            "reply_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "uuid",
            "likes_count",
            "reported_count",
            "reply_count",
            "created_at",
            "updated_at",
        ]


class FeedCommentListSerializer(FeedCommentSerializer):
    """
    피드 댓글 리스트 시리얼라이저:
    피드 댓글의 리스트를 조회
    """

    author = AuthorSerializer(source="user.profile", help_text="작성자")
    is_like = serializers.BooleanField(help_text="좋아요 여부", default=False)
    is_reported = serializers.BooleanField(help_text="신고 여부", default=False)

    class Meta:
        model = FeedComment
        fields = [
            "uuid",
            "author",
            "content",
            "likes_count",
            "reported_count",
            "reply_count",
            "is_deleted",
            "is_like",
            "is_reported",
            "created_at",
            "updated_at",
        ]


class FeedCommentLikeSerializer(serializers.ModelSerializer):
    """
    피드 댓글 좋아요 시리얼라이저:
    좋아요 및 좋아요 취소
    """

    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(), help_text="사용자"
    )
    is_like = serializers.BooleanField(help_text="좋아요 여부", required=True)

    @transaction.atomic
    def update(self, instance, validated_data):
        is_like = validated_data.get("is_like")
        if is_like:
            _, is_create = FeedCommentLike.objects.get_or_create(
                feed_comment=instance, user=validated_data["user"]
            )
            instance.likes_count += 1 if is_create else 0
        else:
            FeedCommentLike.objects.filter(
                feed_comment=instance, user=validated_data["user"]
            ).delete()
            instance.likes_count -= 1 if instance.likes_count > 0 else 0
        instance.save()
        return validated_data

    class Meta:
        model = FeedComment
        fields = [
            "user",
            "is_like",
        ]


class FeedCommentReportSerializer(serializers.ModelSerializer):
    """
    피드 댓글 신고 시리얼라이저:
    피드 댓글 신고
    """

    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(), help_text="사용자"
    )
    report_reason = serializers.ChoiceField(
        choices=FeedReportReason, help_text="신고 사유"
    )
    content = serializers.CharField(
        help_text="내용", required=False, allow_blank=True, allow_null=True
    )

    @transaction.atomic
    def update(self, instance, validated_data):
        # 신고 생성
        try:
            FeedCommentReport.objects.create(feed_comment=instance, **validated_data)
        except IntegrityError:
            raise serializers.ValidationError(E006_COMMENT_ALREADY_REPORTED)
        # 신고 수 증가
        instance.reported_count += 1
        instance.save()
        return validated_data

    class Meta:
        model = FeedComment
        fields = [
            "user",
            "report_reason",
            "content",
        ]
