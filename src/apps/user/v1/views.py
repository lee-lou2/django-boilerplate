from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render, redirect
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django_otp.plugins.otp_totp.models import TOTPDevice
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, mixins, exceptions
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from apps.user.models import UserProfile, UserPreference
from apps.user.v1.serializers import (
    UserProfileSerializer,
    UserPreferenceSerializer,
)

User = get_user_model()


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


def setup_otp_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return render(
            request, "otp/error.html", {"message": "유효하지 않은 링크입니다."}
        )

    device = TOTPDevice.objects.filter(user=user).first()

    # 디바이스 존재 여부 확인
    if not device:
        device = TOTPDevice.objects.create(
            user=user,
            confirmed=False,
            name=f"otp_{user.pk}",
        )

    # 이미 설정된 디바이스인지 확인
    if device.confirmed:
        return render(request, "otp/otp_already_set.html")

    # 설정되지 않은 경우 설정
    if request.method == "GET":
        login(request, user)
        return render(request, "otp/setup_otp.html", {"config_url": device.config_url})

    # 사용자 검증 토큰 일치 여부 확인
    user.last_login = None
    if not default_token_generator.check_token(user, token):
        return render(request, "otp/invalid_link.html")

    # OTP 토큰 일치 여부 확인
    otp_token = request.POST.get("otp_token")
    is_valid = device.verify_token(otp_token)
    if not is_valid:
        messages.error(
            request,
            "OTP 코드가 올바르지 않습니다. 시간을 확인하거나 코드를 다시 입력해주세요.",
        )
        return render(request, "otp/setup_otp.html")

    # OTP 설정 완료
    device.confirmed = True
    device.save()
    user.is_verified = True
    user.is_staff = True
    user.save()
    messages.success(request, "OTP 설정이 완료되었습니다.")
    return redirect("admin:index")
