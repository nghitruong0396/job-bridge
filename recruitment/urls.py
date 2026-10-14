from rest_framework.routers import DefaultRouter

from .views import (
    ApplicationViewSet, CandidateViewSet, JobPostViewSet, ReferralRewardViewSet,
)


app_name = "recruitment"

router = DefaultRouter()
router.register("jobs", JobPostViewSet, basename="job")
router.register("candidates", CandidateViewSet, basename="candidate")
router.register("applications", ApplicationViewSet, basename="application")
router.register("rewards", ReferralRewardViewSet, basename="reward")

urlpatterns = router.urls
