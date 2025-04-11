from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, mixins, exceptions
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from apps.user.models import UserProfile, UserPreference
from apps.user.v1.serializers import (
    UserProfileSerializer,
    UserPreferenceSerializer,
)


class UserProfileViewSet(
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
):
    """사용자 프로필"""

    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # 로그인한 사용자 지정
        return get_object_or_404(self.get_queryset(), user=self.request.user)

    def perform_create(self, serializer):
        # 내 프로필만 등록 가능
        serializer.save(user=self.request.user)

    @extend_schema(
        responses={
            200: UserProfileSerializer,
        },
        tags=["user"],
        summary="사용자 프로필 조회",
        description="""
        로그인한 사용자의 프로필을 조회합니다.
        me로 조회하면 로그인한 사용자의 프로필을 조회합니다.
        """,
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=UserProfileSerializer,
        responses={
            201: UserProfileSerializer,
        },
        tags=["user"],
        summary="사용자 프로필 생성",
        description="""
        로그인한 사용자의 프로필을 생성합니다.
        """,
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        request=UserProfileSerializer,
        responses={
            200: UserProfileSerializer,
        },
        tags=["user"],
        summary="사용자 프로필 수정",
        description="""
        로그인한 사용자의 프로필을 수정합니다.
        me로 수정하면 로그인한 사용자의 프로필을 수정합니다.
        """,
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(exclude=True)
    def partial_update(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("PATCH method not allowed")


class UserPreferenceViewSet(
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
):
    """사용자 선호 정보"""

    queryset = UserPreference.objects.all()
    serializer_class = UserPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """객체 조회"""
        return get_object_or_404(self.get_queryset(), user=self.request.user)

    @extend_schema(
        responses={
            200: UserPreferenceSerializer,
        },
        tags=["user"],
        summary="사용자 선호 정보 상세 조회",
        description="""
        로그인한 사용자의 선호 정보를 조회합니다.
        me로 조회하면 로그인한 사용자의 선호 정보를 조회합니다.
        """,
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("PUT method not allowed")

    @extend_schema(
        request=UserPreferenceSerializer,
        responses={
            200: UserPreferenceSerializer,
        },
        tags=["user"],
        summary="사용자 선호 정보 수정",
        description="""
        로그인한 사용자의 선호 정보를 수정합니다.
        """,
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)
