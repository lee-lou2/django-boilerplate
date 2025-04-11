from django.utils.functional import SimpleLazyObject
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object


class SimpleLazyUser(SimpleLazyObject):
    @property
    def is_authenticated(self):
        """인증 여부: 토큰 인증 시 인증된 사용자로 판단"""
        return True

    def __bool__(self):
        """사용자 존재: Permission 에서 사용자 인증 여부 확인"""
        return True


class JWTLazyUserAuthentication(JWTAuthentication):
    """
    JWT 사용자 지연 인증
    - 토큰 검증을 통해 인증을 진행
    - 데이터베이스에 저장된 사용자 정보는 실제 데이터가 사용되는 곳에서 지연 로딩
    """

    def get_active_user(self, user_id):
        """지연 로딩: 사용자 조회 및 활성화 여부 확인"""
        try:
            user = self.user_model.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except self.user_model.DoesNotExist:
            raise exceptions.AuthenticationFailed(
                _("User not found"), code="user_not_found"
            )
        if api_settings.CHECK_USER_IS_ACTIVE and not user.is_active:
            raise exceptions.AuthenticationFailed(
                _("User is inactive"), code="user_inactive"
            )
        return user

    def get_user(self, validated_token):
        """토큰을 이용한 사용자 조회"""
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise exceptions.InvalidToken(
                _("Token contained no recognizable user identification")
            )
        return SimpleLazyUser(lambda: self.get_active_user(user_id))


class JWTLazyUserAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    drf-spectacular 확장 클래스
    - 인증 확장 클래스 정의
    - 인증 확장 클래스 정의
    """

    target_class = JWTLazyUserAuthentication
    name = "Bearer"

    def get_security_definition(self, auto_schema):
        """인증 확장 클래스 정의"""
        return build_bearer_security_scheme_object(
            header_name="Authorization",
            token_prefix="Bearer",
            bearer_format="JWT",
        )
