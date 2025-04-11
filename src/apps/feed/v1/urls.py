from django.urls import path, include
from rest_framework_nested import routers

from apps.feed.v1.views import (
    FeedViewSet,
    FeedCommentViewSet,
)

router = routers.SimpleRouter()
router.register("feed", FeedViewSet, basename="feed")

feed_router = routers.NestedSimpleRouter(router, r"feed", lookup="feed")
feed_router.register(r"comment", FeedCommentViewSet, basename="feed-comment")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(feed_router.urls)),
]
