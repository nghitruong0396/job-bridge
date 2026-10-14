from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm

from .models import User


class AccountLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email công ty",
        widget=forms.EmailInput(attrs={"autofocus": True}),
    )


class AccountCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "email",
            "employee_code",
            "full_name",
            "department",
            "phone",
            "role",
        )


class AccountChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"
