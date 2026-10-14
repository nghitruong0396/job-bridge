from django.urls import path

from .web_views import AccountLoginView, AccountLogoutView, AccountProfileView


app_name = "accounts_web"

urlpatterns = [
    path("login/", AccountLoginView.as_view(), name="login"),
    path("logout/", AccountLogoutView.as_view(), name="logout"),
    path("profile/", AccountProfileView.as_view(), name="profile"),
]
