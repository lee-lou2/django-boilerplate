from rest_framework.routers import SimpleRouter

from apps.account.v1.views import (
    LoginViewSet,
    RegisterViewSet,
    PasswordViewSet,
    GoogleLoginViewSet,
)

router = SimpleRouter()
router.register("account", LoginViewSet, basename="user")
router.register("account/register", RegisterViewSet, basename="register")
router.register("account/password", PasswordViewSet, basename="password")
router.register("account/google", GoogleLoginViewSet, basename="google_login")

urlpatterns = router.urls
