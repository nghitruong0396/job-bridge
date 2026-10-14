from django.urls import path

from . import web_views


app_name = "recruitment_web"

urlpatterns = [
    path("jobs/", web_views.job_list, name="job-list"),
    path("jobs/create/", web_views.job_form, name="job-create"),
    path("jobs/<int:pk>/", web_views.job_detail, name="job-detail"),
    path("jobs/<int:pk>/edit/", web_views.job_form, name="job-edit"),
    path("jobs/<int:pk>/refer/", web_views.refer_candidate, name="refer"),
    path("jobs/<int:pk>/<str:operation>/", web_views.job_action, name="job-action"),
]
