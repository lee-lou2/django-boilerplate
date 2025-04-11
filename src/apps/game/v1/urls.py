from django.urls import path

from apps.game.v1.views import AttendanceCheckViewSet, AttendanceCheckRoleAPIView

urlpatterns = [
    path(
        "game/attendance-check/",
        AttendanceCheckViewSet.as_view(
            {
                "get": "retrieve",
                "post": "partial_update",
            }
        ),
        name="attendance-check",
    ),
    path(
        "game/attendance-check/role/",
        AttendanceCheckRoleAPIView.as_view(),
        name="attendance-check-role",
    ),
]
