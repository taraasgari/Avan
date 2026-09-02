from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import redirect


def _login_redirect(request):
    return redirect(f"/account/login/?next={request.path}")


def owner_required(view_func):
    """Owner Console gate.

    Superusers always pass. Stage 13 staff accounts pass only when their explicit
    StaffAccess profile grants the section that matches the requested path.
    Unknown Owner Console paths fail closed for non-superusers.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _login_redirect(request)
        if not request.user.is_active:
            return HttpResponseForbidden("Active staff account required.")
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        try:
            from apps.launchops.permissions import staff_can_access_path

            allowed = staff_can_access_path(request.user, request.path)
        except Exception:
            allowed = False
        if not allowed:
            return HttpResponseForbidden("You do not have permission for this Owner Console section.")
        return view_func(request, *args, **kwargs)

    return wrapper


def superuser_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _login_redirect(request)
        if not request.user.is_active or not request.user.is_superuser:
            return HttpResponseForbidden("Superuser access only.")
        return view_func(request, *args, **kwargs)

    return wrapper
