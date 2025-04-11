from rest_framework.routers import SimpleRouter

from apps.agreement.v1.views import (
    AgreementViewSet,
    UserAgreementViewSet,
)

router = SimpleRouter()
router.register(
    "account/agreement",
    AgreementViewSet,
    basename="agreement",
)
router.register(
    "user/me/agreement",
    UserAgreementViewSet,
    basename="user-agreement",
)

urlpatterns = router.urls
