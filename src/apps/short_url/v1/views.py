from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, permissions, viewsets
from rest_framework.generics import get_object_or_404

from apps.short_url.models import ShortUrl
from apps.short_url.v1.serializers import ShortUrlSerializer, ShortUrlRedirectSerializer
from apps.short_url.v1.utils import key_to_id


class ShortUrlViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
):
    """단축 URL 뷰셋"""

    serializer_class = ShortUrlSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=ShortUrlSerializer,
        responses={
            201: ShortUrlSerializer,
        },
        tags=["short-url"],
        summary="단축URL 생성",
        description="""
        단축 URL을 생성합니다.
        4자리 랜덤 키와 id를 문자열로 변경한 값을 결합해 ShortKey를 생성합니다.
        """,
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class ShortUrlRedirectView(generics.RetrieveAPIView):
    """단축 URL 리다이렉트 뷰"""

    serializer_class = ShortUrlRedirectSerializer
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        responses={
            200: ShortUrlRedirectSerializer,
        },
        tags=["short-url"],
        summary="단축URL 리다이렉트",
        description="""
        단축 URL을 리다이렉트합니다.
        """,
    )
    def retrieve(self, request, *args, **kwargs):
        short_url_id = key_to_id(self.kwargs.get("short_key")[2:-2])
        instance = get_object_or_404(ShortUrl, id=short_url_id)
        serializer = self.get_serializer(instance)
        serializer.save()
        return render(request, "short_url/redirect.html", serializer.data)
