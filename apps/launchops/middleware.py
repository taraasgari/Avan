import logging
import time
import uuid

from .models import OwnerAuditEvent


request_logger = logging.getLogger("avan.request")


class RequestTelemetryMiddleware:
    """Attach an opaque request id and emit one structured access-log event."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = (request.headers.get("X-Request-ID") or "").strip()[:64]
        if not request_id:
            request_id = uuid.uuid4().hex
        request.request_id = request_id
        started = time.perf_counter()
        response = self.get_response(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers.setdefault("X-Request-ID", request_id)

        if not request.path.startswith(("/static/", "/media/")):
            request_logger.info(
                "request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.path[:500],
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "user_id": getattr(getattr(request, "user", None), "pk", None),
                },
            )
        return response


class OwnerAuditMiddleware:
    """Persist an audit trail for state-changing Owner Console requests.

    POST bodies are intentionally never copied into the audit table, avoiding
    accidental storage of passwords, tokens, addresses or other sensitive input.
    """

    WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/owner/") and request.method in self.WRITE_METHODS:
            user = getattr(request, "user", None)
            if getattr(user, "is_authenticated", False):
                try:
                    match = getattr(request, "resolver_match", None)
                    action = "owner_write"
                    if match:
                        action = (match.view_name or match.url_name or action)[:80]
                    OwnerAuditEvent.objects.create(
                        actor=user,
                        action=action,
                        path=request.path[:500],
                        method=request.method,
                        status_code=response.status_code,
                        request_id=(getattr(request, "request_id", "") or "")[:64],
                        details={"query_keys": sorted(request.GET.keys())[:30]},
                    )
                except Exception:
                    # Auditing must not take down checkout or Owner Console.
                    pass
        return response
