from django.urls import path
from django.views.generic.base import RedirectView

from . import web_views


app_name = "recruitment_web"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="recruitment_web:job-list", permanent=False), name="home"),
    path("jobs/", web_views.job_list, name="job-list"),
    path("jobs/create/", web_views.job_form, name="job-create"),
    path("jobs/<int:pk>/", web_views.job_detail, name="job-detail"),
    path("jobs/<int:pk>/edit/", web_views.job_form, name="job-edit"),
    path("jobs/<int:pk>/refer/", web_views.refer_candidate, name="refer"),
    path("jobs/<int:pk>/<str:operation>/", web_views.job_action, name="job-action"),
    path("applications/", web_views.application_list, name="application-list"),
    path("applications/<int:pk>/", web_views.application_detail, name="application-detail"),
    path("applications/<int:pk>/stage/", web_views.application_stage, name="application-stage"),
    path("applications/<int:pk>/note/", web_views.application_note, name="application-note"),
    path("applications/<int:pk>/confirm-reward/", web_views.confirm_reward, name="confirm-reward"),
    path("candidates/", web_views.candidate_list, name="candidate-list"),
    path("candidates/<int:pk>/", web_views.candidate_detail, name="candidate-detail"),
    path("candidates/<int:pk>/edit/", web_views.candidate_edit, name="candidate-edit"),
    path("rewards/", web_views.reward_list, name="reward-list"),
]
