from rest_framework.permissions import BasePermission

from .models import User


class IsHR(BasePermission):
    message = "Chỉ HR được thực hiện thao tác này."

    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_authenticated
            and user.is_active
            and user.role == User.Role.HR
        )


class IsEmployee(BasePermission):
    message = "Chỉ Employee được thực hiện thao tác này."

    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_authenticated
            and user.is_active
            and user.role == User.Role.EMPLOYEE
        )
