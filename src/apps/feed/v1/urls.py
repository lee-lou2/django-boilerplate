from django.urls import path, include
from rest_framework_nested import routers

from apps.feed.v1.views import (
    FeedViewSet,
    FeedCommentViewSet,
)

feed_router = routers.SimpleRouter()
feed_router.register("feed", FeedViewSet, basename="feed")

comment_router = routers.NestedSimpleRouter(feed_router, r"feed", lookup="feed")
comment_router.register(r"comment", FeedCommentViewSet, basename="feed-comment")

urlpatterns = [
    path("", include(feed_router.urls)),
    path("", include(comment_router.urls)),
]
