from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def default_exception_handler(exc, context):
    """기본 오류 핸들러"""
    response = exception_handler(exc, context)
    if (
        response is None
        or not hasattr(response, "data")
        or not isinstance(exc, ValidationError)
        or not isinstance(response.data, dict)
    ):
        return response
    # 오류 구조 변경
    for key, value in response.data.items():
        response.data[key] = (
            [{"message": item, "error_code": "E0000000"} for item in value]
            if isinstance(value, list)
            else [value]
        )
    return response
