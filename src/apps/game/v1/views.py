from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, mixins, response, views, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.game.models import AttendanceCheck
from apps.game.v1.serializers import AttendanceCheckSerializer


class AttendanceCheckViewSet(
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
):
    """
    출석 체크:
    하루에 1번 참여 가능한 출석 체크
    총 연속 일수 7일이 주어지며 연속 일수가 높아질수록 지급 포인트도 높아짐
    연속 일수나 지급 포인트는 settings 에서 변경 가능
    """

    queryset = AttendanceCheck.objects.all()
    serializer_class = AttendanceCheckSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # 가장 최근 출석 체크 기록을 조회
        return self.get_queryset().filter(user=self.request.user).last()

    @extend_schema(
        responses={
            200: AttendanceCheckSerializer,
        },
        tags=["game"],
        summary="마지막 출석 체크 조회",
        description="""
        마지막 출석 체크 이력을 조회해서 반환
        """,
    )
    def retrieve(self, request, *args, **kwargs):
        # [Why]
        # Q. 왜 마지막 출석 체크 이력만 반환하는가?
        # A. 마지막 출석 체크일, 연속 일수만 알고 있어도 모든 정보를 얻을 수 있음
        #    연속 미션이 유효한 상태인지,
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
        summary="출석 체크 참여",
        description="""
        오늘 출석 체크를 참여
        """,
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


class AttendanceCheckRoleAPIView(views.APIView):
    """출석 체크 룰"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: list[int],
        },
        tags=["game"],
        summary="출석 체크 룰 조회",
        description="""
        출석 체크 룰을 조회
        """,
    )
    def get(self, request, *args, **kwargs):
        return response.Response(settings.ATTENDANCE_CHECK_REWARD_POINTS)
