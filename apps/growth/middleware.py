import os

from django.db.models import F
from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.utils import timezone

from .models import SeoRedirect
from .security import _event, hit_limit


class AvanSecurityMiddleware:
    """Low-risk request throttles + modern response security headers."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            if request.path.startswith("/api/"):
                blocked, count = hit_limit(request, bucket="api-write", limit=180, window_seconds=60)
                if blocked:
                    _event("api_rate_limited", request, severity="warning", count=count)
                    return HttpResponse("Too many requests.", status=429, content_type="text/plain")
            elif request.path.startswith("/owner/"):
                blocked, count = hit_limit(request, bucket="owner-write", limit=120, window_seconds=60)
                if blocked:
                    _event("owner_rate_limited", request, severity="high", count=count)
                    return HttpResponse("Too many requests.", status=429, content_type="text/plain")

        response = self.get_response(request)

        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=(self)")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")

        csp = (
            "default-src 'self'; "
            "base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'; "
            "img-src 'self' data: blob:; font-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
            "connect-src 'self'; worker-src 'self' blob:; manifest-src 'self'"
        )
        if os.environ.get("AVAN_CSP_ENFORCE", "0") == "1":
            response.headers.setdefault("Content-Security-Policy", csp)
        else:
            response.headers.setdefault("Content-Security-Policy-Report-Only", csp)
        return response


class SeoRedirectMiddleware:
    """Permanent redirects keep link equity when public URLs are changed."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in {"GET", "HEAD"} and not request.path.startswith(("/admin/", "/owner/", "/api/")):
            try:
                redirect = SeoRedirect.objects.filter(old_path=request.path, is_active=True).first()
            except Exception:
                redirect = None
            if redirect and redirect.new_path != request.path:
                try:
                    SeoRedirect.objects.filter(pk=redirect.pk).update(hit_count=F("hit_count") + 1, last_hit_at=timezone.now())
                except Exception:
                    pass
                target = redirect.new_path
                if request.META.get("QUERY_STRING"):
                    target += ("&" if "?" in target else "?") + request.META["QUERY_STRING"]
                return HttpResponsePermanentRedirect(target)
        return self.get_response(request)
