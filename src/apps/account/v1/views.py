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
    User Registration
    Request to register using email address, password, and password confirmation fields.
    Actual registration is completed after email verification.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: RegisterSerializer,
        },
        tags=["account"],
        summary="User Registration - Email, password verification, creation request",
        description="""
        Request to register using email address, password, and password confirmation fields.
        Actual registration is completed after email verification.
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
                description="Hashed email value",
                required=True,
            ),
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Email verification token",
                required=True,
            ),
        ],
        responses={
            302: HttpResponsePermanentRedirect,
        },
        tags=["account"],
        summary="User Registration - Email verification",
        description="""
        Sends a verification code and hashed email via email upon registration.
        Email verification is performed using the received verification code and hashed email.
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
    Login
    Login using email address and password.
    Token renewal using refresh token.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def perform_create(self, serializer):
        # Does not actually save data
        pass

    def get_permissions(self):
        # Authentication is required for logout
        if self.action == "logout":
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: LoginSerializer,
        },
        tags=["account"],
        summary="Login",
        description="""
        Login using email address and password.
        If profile is not registered, redirects to profile page.
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
        summary="Refresh token renewal",
        description="""
        Renews token using refresh token.
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
        summary="Logout",
        description="""
        Logout using token.
        Token is invalidated upon logout.
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
    Password Reset
    Sends a reset link to the email address upon input.
    Changes password when hashed email address, token, and password are provided.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetSerializer

    @extend_schema(
        request=PasswordResetSerializer,
        responses={
            200: PasswordResetSerializer,
        },
        tags=["account"],
        summary="Password reset request",
        description="""
        Sends a password reset link to the email address.
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
        summary="Password change",
        description="""
        Changes password using hashed email address, token, and password.
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
    Social Login - Google
    Redirects to Google login page.
    Handles registration and login using Google login callback information.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = GoogleLoginSerializer

    @extend_schema(
        responses={
            302: HttpResponseRedirect,
        },
        tags=["account"],
        summary="Google Login - Redirect to login page",
        description="""
        Redirects to Google login page.
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
        summary="Google Login",
        description="""
        Google login callback URL.
        Issues token if email is verified.
        Sends verification email if email is not verified.
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
