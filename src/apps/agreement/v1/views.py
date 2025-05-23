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
    """User Agreements"""

    queryset = Agreement.objects.filter(is_active=True)
    serializer_class = AgreementSerializer
    pagination_class = AgreementLimitOffsetPagination
    permission_classes = [AllowAny]

    @extend_schema(
        responses={
            200: AgreementSerializer,
        },
        tags=["account"],
        summary="User Agreement List",
        description="""
        Retrieves the list of user agreements.
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
    """User Agreement Consent"""

    queryset = UserAgreement.objects.filter(agreement__is_active=True)
    serializer_class = UserAgreementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve queryset"""
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        """Retrieve serializer class"""
        if self.action == "create":
            return UserAgreementCreateSerializer
        return super().get_serializer_class()

    @extend_schema(
        responses={
            200: UserAgreementSerializer,
        },
        tags=["user"],
        summary="User Agreement List",
        description="""
        Retrieves the list of user agreements.
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
        summary="User Agreement Consent",
        description="""
        Agrees to the user agreements.
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
        summary="Update User Agreement Consent",
        description="""
        Updates the user agreement consent information.
        """,
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)
