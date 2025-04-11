from django.urls import path

from apps.user.v1.views import (
    UserProfileViewSet,
    UserPreferenceViewSet,
)

urlpatterns = [
    path(
        "user/me/profile/",
        UserProfileViewSet.as_view(
            {
                "get": "retrieve",
                "post": "create",
                "put": "update",
            }
        ),
        name="user-profile",
    ),
    path(
        "user/me/preference/",
        UserPreferenceViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
            }
        ),
        name="user-preference",
    ),
]
