import jwt
from django.conf import settings
from django.core.cache import caches
from django.utils import timezone
from model_bakery import baker
from rest_framework.test import APITestCase as DRFAPITestCase

from users.user.models import User


class APITestCase(DRFAPITestCase):
    def create_user(self, user_data, password_data=None, auth_data=None):
        if password_data is None:
            password_data = {}
        if auth_data is None:
            auth_data = {}
        auth = baker.prepare("users_auth.Auth", **auth_data)
        return User.objects.create_user(
            user_data=user_data,
            password_data=password_data,
            auth_data={
                "bank": auth.bank,
                "phone_no": auth.phone_no,
                "birthday": auth.birthday,
                "adult_auth_at": auth.adult_auth_at,
                "sex": auth.sex,
                "ci": auth.ci,
                "di": auth.di,
                "account_no": auth.account_no,
                "account_owner": auth.account_owner,
            },
            agreement_data={
                "service_agree_at": timezone.localtime(),
                "private_info_agree_at": timezone.localtime(),
            },
        )

    def create_payload(self, token_type, user_random_key_id, uuid):
        iat = timezone.now()
        return {
            "token_type": token_type,
            settings.JWT["USER_ID_CLAIM"]: user_random_key_id,
            "iat": iat,
            "exp": iat + settings.JWT["ACCESS_TOKEN_LIFETIME"],
            "jti": uuid,
            "sub": "user",
            "iss": settings.JWT["ISSUER"],
            "aud": settings.JWT["AUDIENCE"],
        }

    def login(self, user_random_key_id, uuid):
        access_payload = self.create_payload("access", user_random_key_id, uuid)
        access_token = jwt.encode(
            access_payload,
            key=settings.JWT["SIGNING_KEY"],
            algorithm=settings.JWT["ALGORITHM"],
        )

        if user_random_key_id:
            refresh_payload = self.create_payload("refresh", user_random_key_id, uuid)
            refresh_token = jwt.encode(
                refresh_payload,
                key=settings.JWT["SIGNING_KEY"],
                algorithm=settings.JWT["ALGORITHM"],
            )
            caches["user"].set(
                access_token,
                refresh_token,
                settings.JWT["REFRESH_TOKEN_LIFETIME"].total_seconds(),
            )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}", HTTP_X_DEVICE_UUID=uuid
        )
        return access_token
