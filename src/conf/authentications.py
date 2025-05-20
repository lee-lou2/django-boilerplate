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
        """Authentication status: considered authenticated when using token auth"""
        return True

    def __bool__(self):
        """User existence: used by permissions to check authentication"""
        return True


class JWTLazyUserAuthentication(JWTAuthentication):
    """
    JWT lazy user authentication
    - Authenticates using token validation
    - User data stored in the database is lazily loaded where it is actually used
    """

    def get_active_user(self, user_id):
        """Lazy loading: fetch user and check if active"""
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
        """Retrieve user using the token"""
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise exceptions.InvalidToken(
                _("Token contained no recognizable user identification")
            )
        return SimpleLazyUser(lambda: self.get_active_user(user_id))


class JWTLazyUserAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    drf-spectacular extension class
    - Defines the authentication extension
    - Defines the authentication extension
    """

    target_class = JWTLazyUserAuthentication
    name = "Bearer"

    def get_security_definition(self, auto_schema):
        """Define the authentication extension"""
        return build_bearer_security_scheme_object(
            header_name="Authorization",
            token_prefix="Bearer",
            bearer_format="JWT",
        )
