import os

from django.db.models import F
from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.utils import timezone

from .models import SeoRedirect
from .security import _event, hit_limit




def _is_owner_visual_preview(request):
    """Allow same-origin framing only for authenticated superuser visual previews."""
    if request.method not in {"GET", "HEAD"}:
        return False

    if (
        request.GET.get("visual_preview") != "1"
        or request.GET.get("visual_edit") != "1"
    ):
        return False

    user = getattr(request, "user", None)
    if not (
        getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
        and getattr(user, "is_superuser", False)
    ):
        return False

    blocked_prefixes = (
        "/owner/", "/admin/", "/api/", "/bag/", "/checkout/",
        "/orders/", "/payments/", "/login/", "/logout/", "/register/",
    )
    if request.path.startswith(blocked_prefixes):
        return False

    if request.path.startswith("/account/"):
        return (
            request.path in {
                "/account/",
                "/account/profile/",
                "/account/wishlist/",
                "/account/support/",
            }
            or request.path.startswith("/account/support/")
        )

    return True

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

        owner_visual_preview = _is_owner_visual_preview(request)

        # Override Django's DENY only for authenticated owner previews.
        if owner_visual_preview:
            response.headers["X-Frame-Options"] = "SAMEORIGIN"

        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=(self)")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")

        frame_ancestors = "'self'" if owner_visual_preview else "'none'"
        csp = (
            "default-src 'self'; "
            "base-uri 'self'; form-action 'self'; "
            f"frame-ancestors {frame_ancestors}; object-src 'none'; "
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
