from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    class Role(models.TextChoices):
        HR = "HR", "HR / Tuyển dụng"
        EMPLOYEE = "EMPLOYEE", "Nhân viên"

    username = None
    first_name = None
    last_name = None

    employee_code = models.CharField("Mã nhân viên", max_length=30, unique=True)
    email = models.EmailField("Email công ty", unique=True)
    full_name = models.CharField("Họ tên", max_length=150)
    department = models.CharField("Bộ phận", max_length=150, blank=True)
    phone = models.CharField("Số điện thoại", max_length=20, blank=True)
    role = models.CharField(
        "Vai trò",
        max_length=10,
        choices=Role.choices,
        default=Role.EMPLOYEE,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["employee_code", "full_name"]

    class Meta:
        verbose_name = "Tài khoản"
        verbose_name_plural = "Tài khoản"

    def clean(self):
        super().clean()
        self.email = self.email.strip().lower()

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name

    def __str__(self):
        return f"{self.employee_code} - {self.full_name}"
