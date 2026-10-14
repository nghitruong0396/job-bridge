from django.urls import path

from .views import CurrentAccountView, LoginView, LogoutView


app_name = "accounts"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", CurrentAccountView.as_view(), name="me"),
]
