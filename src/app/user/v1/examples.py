from drf_spectacular.utils import OpenApiExample

login_success = OpenApiExample(
    name="로그인 성공 요청",
    request_only=True,
    value={
        "email": "admin@admin.com",
        "password": "admin123!",
    },
)
login_failure = OpenApiExample(
    name="로그인 실패 요청",
    request_only=True,
    value={
        "email": "admin@admin.com",
        "password": "admin123!!",
    },
)
login_examples = [login_success, login_failure]
