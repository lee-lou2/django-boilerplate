from rest_framework.pagination import LimitOffsetPagination


class AgreementLimitOffsetPagination(LimitOffsetPagination):
    """약관 페이지네이션"""

    ordering = ["-order"]
    default_limit = 10
    max_limit = 100
