import enum
import hashlib
import uuid

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


class EmailTemplate(enum.Enum):
    """이메일 템플릿"""

    SIGNUP = (
        "회원 가입 인증",
        settings.SIGNUP_CONFIRM_URL,
        "account/signup.html",
    )
    RESET_PASSWORD = (
        "패스워드 재설정",
        settings.RESET_PASSWORD_URL,
        "account/reset_password.html",
    )


def send_email_verification_token(email: str, template_type: EmailTemplate) -> dict:
    """이메일 검증 토큰 발송"""
    if not email:
        return {}

    # 검증 키 생성 및 설정
    token = uuid.uuid4().hex
    django_env = settings.DJANGO_ENVIRONMENT
    hash_input = (email + settings.EMAIL_VERIFICATION_HASH_SALT).encode("utf-8")
    hashed_email = hashlib.md5(hash_input).hexdigest()
    cache_key = f"email_verification:{django_env}:{hashed_email}"
    cache.set(
        cache_key,
        {"token": token, "email": email},
        timeout=settings.EMAIL_VERIFICATION_TIMEOUT,
    )

    # 이메일 내용 생성
    subject, base_url, template_path = template_type.value
    verification_url = f"{base_url}?hashed_email={hashed_email}&token={token}"
    context = {"url": mark_safe(verification_url)}
    html_message = render_to_string(template_path, context)

    # 이메일 발송
    send_mail(
        subject=subject,
        message="",
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )
    return {"hashed_email": hashed_email, "token": token}


def get_cached_email_verification_data(hashed_email: str) -> dict:
    """캐시된 이메일 검증 데이터 조회"""
    if not hashed_email:
        return {}
    django_env = settings.DJANGO_ENVIRONMENT
    cache_key = f"email_verification:{django_env}:{hashed_email}"
    return cache.get(cache_key, {})
