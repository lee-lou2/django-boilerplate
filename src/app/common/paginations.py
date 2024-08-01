from collections import OrderedDict
from urllib import parse

from django.utils.encoding import force_str
from rest_framework import pagination
from rest_framework.response import Response


class LimitOffsetPagination(pagination.LimitOffsetPagination):
    default_limit = 20
    max_limit = 100

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.count),
                    ("is_next", self.offset + self.limit < self.count),
                    ("results", data),
                ]
            )
        )

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                },
                "is_next": {
                    "type": "boolean",
                },
                "results": schema,
            },
        }


class CursorPagination(pagination.CursorPagination):
    page_size = 20
    max_page_size = 100
    page_size_query_param = "limit"
    ordering = None

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        return ordering + ("pk",)

    def paginate_queryset(self, queryset, request, view=None):
        self.count = self.get_count(queryset)
        return super().paginate_queryset(queryset, request, view)

    def get_count(self, queryset):
        try:
            return queryset.count()
        except (AttributeError, TypeError):
            return len(queryset)

    def encode_cursor(self, cursor):
        url = super().encode_cursor(cursor)
        query = parse.urlsplit(force_str(url)).query
        query_dict = dict(parse.parse_qsl(query, keep_blank_values=True))

        return query_dict.get(self.cursor_query_param)

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.count),
                    ("cursor", self.get_next_link()),
                    ("results", data),
                ]
            )
        )

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                },
                "cursor": {
                    "type": "string",
                    "nullable": True,
                },
                "results": schema,
            },
        }
