from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView

from .forms import AccountLoginForm


class AccountLoginView(LoginView):
    authentication_form = AccountLoginForm
    template_name = "accounts/login.html"
    next_page = "accounts_web:profile"
    redirect_authenticated_user = True


class AccountLogoutView(LogoutView):
    next_page = "accounts_web:login"


class AccountProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"
    login_url = "accounts_web:login"
