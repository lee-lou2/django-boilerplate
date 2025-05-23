from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import views, viewsets, mixins, exceptions, response
from rest_framework.permissions import IsAuthenticated

from apps.game.models import AttendanceCheck
from apps.game.v1.serializers import AttendanceCheckSerializer


class AttendanceCheckViewSet(
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
):
    """
    Attendance Check:
    Allows participation once a day.
    A total of 7 consecutive days are given, and the higher the consecutive days, the higher the points awarded.
    Consecutive days and awarded points can be changed in settings.
    """

    queryset = AttendanceCheck.objects.all()
    serializer_class = AttendanceCheckSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Retrieve the most recent attendance check record
        return self.get_queryset().filter(user=self.request.user).last()

    @extend_schema(
        responses={
            200: AttendanceCheckSerializer,
        },
        tags=["game"],
        summary="Retrieve Last Attendance Check",
        description="""
        Retrieves and returns the last attendance check history.
        """,
    )
    def retrieve(self, request, *args, **kwargs):
        # [Why]
        # Q. Why return only the last attendance check history?
        # A. Knowing only the last check-in date and consecutive days is enough to get all information,
        #    such as whether the consecutive mission is still valid.
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(exclude=True)
    def update(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("PUT method is not allowed.")

    @extend_schema(
        request=None,
        responses={
            200: AttendanceCheckSerializer,
        },
        tags=["game"],
        summary="Participate in Attendance Check",
        description="""
        Participates in today's attendance check.
        """,
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


class AttendanceCheckRoleAPIView(views.APIView):
    """Attendance Check Rules"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: list[int],
        },
        tags=["game"],
        summary="Retrieve Attendance Check Rules",
        description="""
        Retrieves the attendance check rules.
        """,
    )
    def get(self, request, *args, **kwargs):
        return response.Response(settings.ATTENDANCE_CHECK_REWARD_POINTS)
