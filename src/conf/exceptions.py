from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def default_exception_handler(exc, context):
    """Default exception handler"""
    response = exception_handler(exc, context)
    if (
        response is None
        or not hasattr(response, "data")
        or not isinstance(exc, ValidationError)
        or not isinstance(response.data, dict)
    ):
        return response
    # Change error structure
    for key, value in response.data.items():
        response.data[key] = (
            [{"message": item, "error_code": "E0000000"} for item in value]
            if isinstance(value, list)
            else [value]
        )
    return response
