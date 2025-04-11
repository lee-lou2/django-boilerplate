import json
import logging
import secrets

from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from rest_framework import exceptions

from apps.user.models import User, SocialUser, UserProfile

logger = logging.getLogger(__name__)


class SocialLoginAdapter:
    """
    소셜 로그인 어댑터의 기본 클래스:
    현재 구글 로그인만 구현된 상태
    추후 다른 소셜 로그인이 추가될 경우 해당 클래스를 상속받아 구현
    """

    def __init__(self, request):
        self.request = request
        self.provider = None

    def get_redirect_uri(self):
        raise NotImplementedError("Subclasses must implement this method")

    def get_token(self, code: str):
        raise NotImplementedError("Subclasses must implement this method")

    def get_user_data(self, credentials):
        raise NotImplementedError("Subclasses must implement this method")

    def process_user(self, user_data: dict):
        raise NotImplementedError("Subclasses must implement this method")


class GoogleLoginAdapter(SocialLoginAdapter):
    """
    Google 소셜 로그인 어댑터:
    구글 로그인에 필요한 최소한만 구현하기 위해 아래와 같이 구현
    구글 로그인 페이지로 이동
    로그인 결과로 반환 받은 code 를 이용해서 토큰 생성 및 사용자 정보 조회
    조회된 내용으로 계정 생성 등을 진행
    계정 생성 시 이메일을 기준으로 생성하며 인증 여부에 따라 다르게 처리
    """

    # Google OAuth2 클라이언트 설정
    FROM_CLIENT_CONFIG = {
        "client_config": settings.GOOGLE_CLIENT_SECRETS_CONFIG,
        "scopes": [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }

    def __init__(self, request):
        super().__init__(request)
        self.provider = "google"

    def get_redirect_uri(self):
        flow = Flow.from_client_config(**self.FROM_CLIENT_CONFIG)
        # CSRF 방지 state 생성 및 세션 저장
        state = secrets.token_urlsafe(16)
        self.request.session["oauth_state"] = state
        return flow.authorization_url(access_type="offline", state=state)[0]

    def get_token(self, code: str):
        """구글 토큰 발급"""
        flow = Flow.from_client_config(**self.FROM_CLIENT_CONFIG)
        flow.fetch_token(code=code)
        return flow.credentials

    def get_user_data(self, credentials) -> dict:
        """사용자 조회"""
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
        # 필수 데이터 확인
        if not id_info.get("email"):
            raise exceptions.APIException("Email not found in ID token")
        if not id_info.get("email_verified"):
            id_info["email_verified"] = False
        return id_info

    def process_user(self, user_data: dict):
        """조회된 사용자에 대한 처리"""
        email = user_data["email"]
        email_verified = user_data["email_verified"]

        # 사용자 생성/조회
        # [Why]
        # Q. 이메일 인증 여부를 확인하는 이유?
        # A. 이메일 인증 여부에 따라 사용자의 가입 상태를 결정하기 위함
        # Q. get_or_create 를 사용하는 이유?
        # A. 소셜, 기본 방식으로 이미 가입된 경우 생성하지 않고 사용자 조회
        user, is_create = User.objects.get_or_create(
            email=email,
            defaults={"is_verified": bool(email_verified)},
        )
        # 소셜 사용자 생성 또는 업데이트
        # [Why]
        # Q. 소셜 사용자를 생성하는 이유?
        # A. 소셜 로그인 가입 여부를 확인하고 소셜 사용자 정보를 저장하기 위함
        SocialUser.objects.get_or_create(
            user=user,
            provider=self.provider,
            social_id=user_data["sub"],
            defaults={"user_data": json.dumps(user_data)},
        )
        # 사용자 프로필 생성 또는 업데이트
        # [Why]
        # Q. 사용자 프로필을 생성하는 이유?
        # A. 사용자 프로필 정보를 저장하기 위함
        # Q. get_or_create 를 사용하는 이유?
        # A. 프로필이 없는 경우 신규 생성하기 위함, 있다면 생성하지 않음
        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "nickname": user_data.get("name"),
                "image": user_data.get("picture"),
            },
        )
        if is_create:
            # 신규 생성 시 비밀번호 미사용
            user.set_unusable_password()
            user.save()
            return user
        # 이메일 인증 여부 업데이트
        # [Why]
        # Q. 이메일 인증 여부를 업데이트 하는 이유?
        # A. 이미 가입된 사용자 중 인증하지 않은 사용자일 경우 소셜에서 인증되어있다면 자동 인증
        final_verified_status = user.is_verified or email_verified
        if user.is_verified != final_verified_status:
            user.is_verified = final_verified_status
            user.save(update_fields=["is_verified"])
        return user
