from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse


def owner_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/account/login/?next={request.path}")
        if not request.user.is_active or not request.user.is_superuser:
            return HttpResponseForbidden("Owner access only.")
        return view_func(request, *args, **kwargs)

    return wrapper
