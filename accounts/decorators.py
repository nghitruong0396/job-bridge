from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    def decorator(view):
        @login_required(login_url="accounts_web:login")
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_active or request.user.role not in roles:
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapped

    return decorator
