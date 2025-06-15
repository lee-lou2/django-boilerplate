from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, mixins, generics, permissions
from rest_framework.generics import get_object_or_404

from apps.short_url.models import ShortUrl
from apps.short_url.v1.serializers import ShortUrlSerializer, ShortUrlRedirectSerializer
from apps.short_url.v1.utils import key_to_id


class ShortUrlViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
):
    """Short URL ViewSet"""

    serializer_class = ShortUrlSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=ShortUrlSerializer,
        responses={
            201: ShortUrlSerializer,
        },
        tags=["short-url"],
        summary="Create Short URL",
        description="""
        Creates a short URL.
        Generates a ShortKey by combining a 4-character random key and the ID converted to a string.
        """,
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class ShortUrlRedirectView(generics.RetrieveAPIView):
    """Short URL Redirect View"""

    serializer_class = ShortUrlRedirectSerializer
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        responses={
            200: ShortUrlRedirectSerializer,
        },
        tags=["short-url"],
        summary="Redirect Short URL",
        description="""
        Redirects the short URL.
        """,
    )
    def retrieve(self, request, *args, **kwargs):
        short_url_id = key_to_id(self.kwargs.get("short_key")[2:-2])
        instance = get_object_or_404(ShortUrl, id=short_url_id)
        serializer = self.get_serializer(instance)
        serializer.save()
        return render(request, "short_url/redirect.html", serializer.data)
