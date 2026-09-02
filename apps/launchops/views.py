import hmac
import os
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from apps.owner.decorators import superuser_required

from .models import OwnerAuditEvent, StaffAccess
from .status import cache_ready, collect_launch_checks, database_ready


@require_GET
@never_cache
def live(request):
    return JsonResponse({"status": "ok"})


@require_GET
@never_cache
def ready(request):
    ok = database_ready()
    # Redis/cache is auxiliary by architecture; only make it readiness-critical
    # when deployment explicitly requires Redis cache.
    if os.environ.get("ENABLE_REDIS_CACHE", "0") == "1":
        ok = ok and cache_ready()
    return JsonResponse({"status": "ok" if ok else "unavailable"}, status=200 if ok else 503)


@require_GET
@never_cache
def metrics(request):
    expected = os.environ.get("AVAN_METRICS_TOKEN", "")
    supplied = request.headers.get("X-AVAN-Metrics-Token", "")
    if len(expected) < 32 or not hmac.compare_digest(expected, supplied):
        raise Http404

    from apps.growth.models import ContentReport, SecurityEvent
    from apps.orders.models import Order

    now = timezone.now()
    high_security = SecurityEvent.objects.filter(
        severity=SecurityEvent.Severity.HIGH,
        created_at__gte=now - timedelta(hours=24),
    ).count()
    open_reports = ContentReport.objects.filter(
        status__in=[ContentReport.Status.OPEN, ContentReport.Status.REVIEWING]
    ).count()
    pending_orders = Order.objects.filter(status=Order.Status.PENDING_PAYMENT).count()
    needs_review = Order.objects.filter(status=Order.Status.NEEDS_REVIEW).count()

    lines = [
        "# HELP avan_up AVAN application process is serving requests.",
        "# TYPE avan_up gauge",
        "avan_up 1",
        "# TYPE avan_orders_pending gauge",
        f"avan_orders_pending {pending_orders}",
        "# TYPE avan_orders_needs_review gauge",
        f"avan_orders_needs_review {needs_review}",
        "# TYPE avan_security_high_24h gauge",
        f"avan_security_high_24h {high_security}",
        "# TYPE avan_moderation_open gauge",
        f"avan_moderation_open {open_reports}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; version=0.0.4; charset=utf-8")


def _owner_context(request, **extra):
    from apps.owner.views import _owner_context as owner_context
    return owner_context(request, **extra)


@superuser_required
def launch_dashboard(request):
    checks = collect_launch_checks(include_dependencies=True)
    critical_failures = sum(1 for check in checks if check.critical and not check.ok)
    warnings = sum(1 for check in checks if not check.critical and not check.ok)
    user_model = get_user_model()
    return render(
        request,
        "owner/launch.html",
        _owner_context(
            request,
            checks=checks,
            critical_failures=critical_failures,
            warnings=warnings,
            staff_profiles=StaffAccess.objects.count(),
            active_staff=user_model.objects.filter(is_staff=True, is_active=True).count(),
            recent_audit=OwnerAuditEvent.objects.select_related("actor")[:12],
            version=os.environ.get("AVAN_RELEASE", "development"),
            commit_sha=os.environ.get("AVAN_COMMIT_SHA", "")[:12],
        ),
    )


@superuser_required
def audit_log(request):
    action = (request.GET.get("action") or "").strip()
    actor = (request.GET.get("actor") or "").strip()
    qs = OwnerAuditEvent.objects.select_related("actor")
    if action:
        qs = qs.filter(action=action)
    if actor:
        qs = qs.filter(actor__username__icontains=actor)
    actions = list(OwnerAuditEvent.objects.values_list("action", flat=True).distinct().order_by("action")[:100])
    return render(
        request,
        "owner/audit.html",
        _owner_context(request, events=qs[:300], actions=actions, selected_action=action, actor_query=actor),
    )
