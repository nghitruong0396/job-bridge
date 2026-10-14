from django.conf import settings
from django.contrib.auth.backends import ModelBackend


class CompanyEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = username if username is not None else kwargs.get("email")
        if email is not None:
            username = email.strip().lower()

        return super().authenticate(
            request, username=username, password=password, **kwargs
        )

    def user_can_authenticate(self, user):
        if not super().user_can_authenticate(user):
            return False

        email = user.email.strip().lower()
        company_domain = settings.COMPANY_EMAIL_DOMAIN
        return (
            bool(company_domain)
            and email.count("@") == 1
            and email.split("@")[0] != ""
            and email.split("@")[1] == company_domain
        )
