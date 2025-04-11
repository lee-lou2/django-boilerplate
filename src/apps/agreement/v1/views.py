from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, mixins, exceptions
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.agreement.models import Agreement, UserAgreement
from apps.agreement.v1.paginations import AgreementLimitOffsetPagination
from apps.agreement.v1.serializers import (
    AgreementSerializer,
    UserAgreementSerializer,
    UserAgreementCreateSerializer,
)


class AgreementViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
):
    """사용자 약관"""

    queryset = Agreement.objects.filter(is_active=True)
    serializer_class = AgreementSerializer
    pagination_class = AgreementLimitOffsetPagination
    permission_classes = [AllowAny]

    @extend_schema(
        responses={
            200: AgreementSerializer,
        },
        tags=["account"],
        summary="사용자 약관 목록",
        description="""
        사용자 약관 목록을 조회합니다.
        """,
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class UserAgreementViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
):
    """사용자 약관 동의"""

    queryset = UserAgreement.objects.filter(agreement__is_active=True)
    serializer_class = UserAgreementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """쿼리셋 조회"""
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        """시리얼라이저 클래스 조회"""
        if self.action == "create":
            return UserAgreementCreateSerializer
        return super().get_serializer_class()

    @extend_schema(
        responses={
            200: UserAgreementSerializer,
        },
        tags=["user"],
        summary="사용자 약관 목록",
        description="""
        사용자 약관 목록을 조회합니다.
        """,
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        request=UserAgreementCreateSerializer,
        responses={
            201: UserAgreementCreateSerializer,
        },
        tags=["user"],
        summary="사용자 약관 동의",
        description="""
        사용자 약관에 동의합니다. 
        """,
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(exclude=True)
    def update(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("PUT method not allowed")

    @extend_schema(
        request=UserAgreementSerializer,
        responses={
            200: UserAgreementSerializer,
        },
        tags=["user"],
        summary="사용자 약관 동의 업데이트",
        description="""
        사용자 약관 동의 정보를 업데이트합니다.
        """,
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)
