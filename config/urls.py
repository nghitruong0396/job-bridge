from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.web_urls")),
    path("", include("recruitment.web_urls")),
    path("api/accounts/", include("accounts.urls")),
    path("api/recruitment/", include("recruitment.urls")),
    path("api-auth/", include("rest_framework.urls")),
]
