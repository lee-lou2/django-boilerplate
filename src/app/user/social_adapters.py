from urllib import parse

import requests
from django.conf import settings
from rest_framework.exceptions import ValidationError


class SocialAdapter:
    key = None

    def __init__(self, code, origin=None):
        self.code = code
        self.origin = origin

    def get_social_user_id(self):
        raise NotImplementedError("Not Implemented 'get_social_user_id' method")


class GoogleAdapter(SocialAdapter):
    key = "google"

    def get_social_user_id(self):
        url = "https://oauth2.googleapis.com/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": f"{self.origin}{settings.SOCIAL_REDIRECT_PATH}",
            "code": parse.unquote(self.code),
        }
        response = requests.post(url=url, data=data)
        if not response.ok:
            raise ValidationError("GOOGLE GET TOKEN API ERROR")
        data = response.json()

        # 사용자 고유 정보 조회
        url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {data.get('access_token', '')}"}
        response = requests.get(url, headers=headers)
        if not response.ok:
            raise ValidationError("GOOGLE ME API ERROR")
        return response.json()["id"]
