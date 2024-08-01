from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import mixins, serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from app.user.models import User
from app.user.v1.serializers import (
    UserLoginSerializer,
    UserLogoutSerializer,
    UserPasswordResetConfirmSerializer,
    UserPasswordResetSerializer,
    UserRefreshSerializer,
    UserRegisterSerializer,
    UserSerializer,
    UserSocialLoginSerializer,
)


@extend_schema_view(
    retrieve=extend_schema(summary="유저 조회"),
    delete=extend_schema(summary="유저 삭제(탈퇴)"),
    login=extend_schema(summary="유저 로그인"),
    swagger_login=extend_schema(exclude=True),
    social_login=extend_schema(
        summary="유저 소셜 로그인",
        responses={
            200: UserSocialLoginSerializer,
            400: inline_serializer(
                name="UserSocialLoginValidationError",
                fields={
                    "social_token": serializers.CharField(
                        required=False, label="소셜 로그인 토큰"
                    ),
                    "non_field": serializers.ListField(
                        required=False, child=serializers.CharField()
                    ),
                    "code": serializers.ListField(
                        required=False, child=serializers.CharField()
                    ),
                    "state": serializers.ListField(
                        required=False, child=serializers.CharField()
                    ),
                },
            ),
        },
    ),
    logout=extend_schema(summary="유저 로그아웃"),
    refresh=extend_schema(summary="유저 리프레시"),
    register=extend_schema(summary="유저 회원가입"),
    password_reset=extend_schema(summary="유저 비밀번호 초기화 메일 발송"),
    password_reset_confirm=extend_schema(summary="유저 비밀번호 재설정"),
)
class UserViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_value_regex = "me"

    def get_object(self):
        if self.kwargs.get("pk") == "me":
            return self.queryset.get(id=self.request.user.id)
        return super().get_object()

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def _create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        methods=["POST"],
        detail=False,
        serializer_class=UserLoginSerializer,
        permission_classes=[],
    )
    def login(self, request, *args, **kwargs):
        return self._create(request, *args, **kwargs)

    @action(
        methods=["POST"],
        detail=False,
        serializer_class=UserSocialLoginSerializer,
        permission_classes=[],
    )
    def social_login(self, request, *args, **kwargs):
        """
        ![social_login_flow]({settings.STATIC_URL}docs/social_login_flow.jpeg)
        1. 소셜 로그인(인가코드 발급)
            - Method: `GET`
            - Url: 각 소셜 로그인 문서 참고
            - Parameter:
                - `client_id`: 앱 ID
                - `redirect_uri`: 인가 코드를 전달받을 프런트 URI(redirect_uri는 소셜 앱 설정에 등록해야합니다.)
                - `response_type`: `code`로 고정
                - `state`: `kakao` | `naver` | `google` | `apple` | `facebook`
            - Description:
                - 소셜 로그인을 진행할 페이지를 띄워야 하기 때문에 route를 이동해줘야 합니다.
                - `redirect_uri`는 소셜 로그인 후 돌아올 프런트 URI이며 쿼리 스트링과 함께 리턴 받습니다.
                - 소셜 로그인 후 해당 페이지에서 쿼리 스트링의 code와 state를 읽어 저장해둔다.
        2. 소셜 로그인(인가코드 검증)
        3. 소셜 회원가입
            - `isRegister: true`인 경우 `access`, `refresh`를 저장 후 로그인 처리를 합니다.
            - `isRegister: false`인 경우 `socialToken`을 사용해 회원가입을 진행합니다.
        """
        return self._create(request, *args, **kwargs)

    @action(methods=["POST"], detail=False, serializer_class=UserLogoutSerializer)
    def logout(self, request, *args, **kwargs):
        """
        모바일앱에서만 사용하며, 유저와 디바이스 토큰의 연결을 끊어주기위해 사용합니다.
        """
        return self._create(request, *args, **kwargs)

    @action(
        methods=["POST"],
        detail=False,
        serializer_class=UserRefreshSerializer,
        permission_classes=[],
    )
    def refresh(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

    @action(
        methods=["POST"],
        detail=False,
        serializer_class=UserRegisterSerializer,
        permission_classes=[],
    )
    def register(self, request, *args, **kwargs):
        """
        소셜 유저인 경우 `socialToken`을 전달해야합니다.
        """
        return self._create(request, *args, **kwargs)

    @action(
        methods=["POST"],
        detail=False,
        serializer_class=UserPasswordResetSerializer,
        permission_classes=[],
    )
    def password_reset(self, request, *args, **kwargs):
        """
        이메일을 통해 비밀번호 재설정 가능한 link을 발급받습니다.
        """
        return self._create(request, *args, **kwargs)

    @action(
        methods=["POST"],
        detail=False,
        serializer_class=UserPasswordResetConfirmSerializer,
        permission_classes=[],
    )
    def password_reset_confirm(self, request, *args, **kwargs):
        """
        유저 비밀번호 초기화 메일 발송 API를 통해 발급 받은 link를 통해 비밀번호를 재설정합니다.
        """
        return self._create(request, *args, **kwargs)
