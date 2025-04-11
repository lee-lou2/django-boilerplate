import logging
from urllib.parse import quote_plus

from django.conf import settings
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import redirect
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, exceptions, response
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action

from apps.account.v1.adapters import GoogleLoginAdapter
from apps.account.v1.serializers import (
    RegisterSerializer,
    EmailVerificationSerializer,
    LoginSerializer,
    RefreshTokenSerializer,
    LogoutSerializer,
    PasswordChangeSerializer,
    PasswordResetSerializer,
    GoogleLoginSerializer,
)

logger = logging.getLogger(__name__)


class RegisterViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
):
    """
    회원 가입
    이메일 주소와 패스워드, 패스워드 확인 필드를 이용해서 회원 가입 신청
    실제 회원 가입은 이메일 검증 이후 완료
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: RegisterSerializer,
        },
        tags=["account"],
        summary="회원 가입 - 이메일, 패스워드 검증, 생성 요청",
        description="""
        이메일 주소와 패스워드, 패스워드 확인 필드를 이용해서 회원 가입 신청합니다.
        실제 회원 가입은 이메일 검증 이후 완료됩니다.
        """,
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="hashed_email",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="해시된 이메일 값",
                required=True,
            ),
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="이메일 인증 토큰",
                required=True,
            ),
        ],
        responses={
            302: HttpResponsePermanentRedirect,
        },
        tags=["account"],
        summary="회원 가입 - 이메일 검증",
        description="""
        회원 가입 시 이메일을 통해 검증 코드와 해시된 이메일을 발송합니다.
        여기서 받은 검증 코드와 해시된 이메일을 통해 이메일 검증을 수행합니다.
        """,
    )
    @action(detail=False, methods=["GET"], serializer_class=EmailVerificationSerializer)
    def confirm(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        encoded_email = quote_plus(serializer.data["email"])
        return redirect(f"{settings.SIGNUP_COMPLETED_URL}?email={encoded_email}")


class LoginViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
):
    """
    로그인
    이메일 주소와 패스워드를 이용해서 로그인
    리프래시 토큰을 이용한 토큰 갱신
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def perform_create(self, serializer):
        # 실제 데이터 저장은 하지 않음
        pass

    def get_permissions(self):
        # 로그아웃 시 인증이 필요함
        if self.action == "logout":
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: LoginSerializer,
        },
        tags=["account"],
        summary="로그인",
        description="""
        이메일 주소와 패스워드를 이용해서 로그인합니다.
        프로필이 등록되어이 있지 않은 경우 프로필 페이지로 이동됩니다.
        """,
    )
    @action(detail=False, methods=["POST"])
    def login(self, request, *args, **kwargs):
        resp = super().create(request, *args, **kwargs)
        resp.status_code = status.HTTP_200_OK
        return resp

    @extend_schema(
        request=RefreshTokenSerializer,
        responses={
            200: RefreshTokenSerializer,
        },
        tags=["account"],
        summary="리프래시 토큰 갱신",
        description="""
        리프래시 토큰을 이용해서 토큰을 갱신합니다.
        """,
    )
    @action(detail=False, methods=["POST"], serializer_class=RefreshTokenSerializer)
    def refresh(self, request, *args, **kwargs):
        resp = super().create(request, *args, **kwargs)
        resp.status_code = status.HTTP_200_OK
        return resp

    @extend_schema(
        request=LogoutSerializer,
        responses={
            204: None,
        },
        tags=["account"],
        summary="로그아웃",
        description="""
        토큰을 이용해서 로그아웃합니다.
        로그아웃 시 토큰이 무효화됩니다.
        """,
    )
    @action(detail=False, methods=["POST"], serializer_class=LogoutSerializer)
    def logout(self, request, *args, **kwargs):
        resp = super().create(request, *args, **kwargs)
        resp.status_code = status.HTTP_204_NO_CONTENT
        resp.data = None
        return resp

    @extend_schema(exclude=True)
    def create(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("POST method not allowed")


class PasswordViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
):
    """
    비밀번호 초기화
    이메일 주소 입력 시 해당 메일로 초기화 링크 전달
    해시 이메일 주소, 토큰, 그리고 비밀번호를 전달하면 변경
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetSerializer

    @extend_schema(
        request=PasswordResetSerializer,
        responses={
            200: PasswordResetSerializer,
        },
        tags=["account"],
        summary="비밀번호 초기화 요청",
        description="""
        이메일 주소로 비밀번호 초기화 링크를 전달합니다.
        """,
    )
    @action(detail=False, methods=["POST"])
    def reset(self, request, *args, **kwargs):
        resp = super().create(request, *args, **kwargs)
        resp.status_code = status.HTTP_200_OK
        return resp

    @extend_schema(
        request=PasswordChangeSerializer,
        responses={
            200: PasswordChangeSerializer,
        },
        tags=["account"],
        summary="비밀번호 변경",
        description="""
        해싱된 이메일 주소, 토큰, 비밀번호를 이용해서 비밀번호를 변경합니다.
        """,
    )
    @action(detail=False, methods=["POST"], serializer_class=PasswordChangeSerializer)
    def change(self, request, *args, **kwargs):
        resp = super().create(request, *args, **kwargs)
        resp.status_code = status.HTTP_200_OK
        return resp

    @extend_schema(exclude=True)
    def create(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("POST method not allowed")


class GoogleLoginViewSet(viewsets.GenericViewSet):
    """
    소셜 로그인 - 구글
    구글 로그인 페이지로 이동
    구글 로그인 콜백 정보로 가입 및 로그인 처리 등
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = GoogleLoginSerializer

    @extend_schema(
        responses={
            302: HttpResponseRedirect,
        },
        tags=["account"],
        summary="구글 로그인 - 로그인 페이지로 이동",
        description="""
        구글 로그인 페이지로 이동합니다.
        """,
    )
    @action(detail=False, methods=["get"], url_path="login")
    def login(self, request, *args, **kwargs):
        redirect_uri = GoogleLoginAdapter(request).get_redirect_uri()
        return redirect(redirect_uri)

    @extend_schema(
        responses={
            200: GoogleLoginSerializer,
        },
        tags=["account"],
        summary="구글 로그인",
        description="""
        구글 로그인 콜백 URL입니다.
        인증된 이메일인 경우 토큰을 발급합니다.
        인증되지 않은 이메일인 경우 인증 메일을 발송합니다.
        """,
    )
    @action(detail=False, methods=["GET"], serializer_class=GoogleLoginSerializer)
    def callback(self, request, *args, **kwargs):
        data = {
            "code": request.GET.get("code"),
            "state": request.GET.get("state"),
            "oauth_state": request.session.pop("oauth_state", None),
        }
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data)
