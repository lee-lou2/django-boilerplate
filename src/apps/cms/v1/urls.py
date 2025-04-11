from rest_framework.routers import SimpleRouter

from apps.cms.v1.views import NoticeViewSet, EventViewSet, FaqViewSet

router = SimpleRouter()
router.register("cms/notice", NoticeViewSet, basename="cms-notice")
router.register("cms/event", EventViewSet, basename="cms-event")
router.register("cms/faq", FaqViewSet, basename="cms-faq")

urlpatterns = router.urls
