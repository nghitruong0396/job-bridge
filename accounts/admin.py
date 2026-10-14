from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import AccountChangeForm, AccountCreationForm
from .models import User


@admin.register(User)
class AccountAdmin(UserAdmin):
    add_form = AccountCreationForm
    form = AccountChangeForm

    list_display = (
        "employee_code",
        "email",
        "full_name",
        "department",
        "role",
        "is_active",
        "is_staff",
    )
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("employee_code", "email", "full_name", "department", "phone")
    ordering = ("employee_code",)
    readonly_fields = ("last_login", "date_joined")

    fieldsets = (
        ("Đăng nhập", {"fields": ("email", "password")}),
        (
            "Thông tin nhân viên",
            {"fields": ("employee_code", "full_name", "department", "phone")},
        ),
        (
            "Vai trò và quyền truy cập",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Thời gian", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            "Tạo tài khoản",
            {
                "fields": (
                    "email",
                    "employee_code",
                    "full_name",
                    "department",
                    "phone",
                    "role",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                )
            },
        ),
    )
