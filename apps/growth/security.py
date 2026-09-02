import hashlib
import io
import os
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

from .models import SecurityEvent


MAX_IMAGE_PIXELS = int(os.environ.get("AVAN_MAX_IMAGE_PIXELS", "40000000"))
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


def client_ip(request):
    """Do not trust X-Forwarded-For unless deployment explicitly opts in."""
    if os.environ.get("AVAN_TRUST_X_FORWARDED_FOR", "0") == "1":
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()
    return request.META.get("REMOTE_ADDR", "") or "unknown"


def ip_hash(request):
    value = client_ip(request)
    salt = str(settings.SECRET_KEY)[:32]
    return hashlib.sha256(f"{salt}|{value}".encode("utf-8")).hexdigest()


def _event(kind, request=None, severity=SecurityEvent.Severity.INFO, **details):
    try:
        SecurityEvent.objects.create(
            kind=kind,
            severity=severity,
            user=getattr(request, "user", None) if getattr(getattr(request, "user", None), "is_authenticated", False) else None,
            ip_hash=ip_hash(request) if request is not None else "",
            path=(getattr(request, "path", "") or "")[:500] if request is not None else "",
            details=details,
        )
    except Exception:
        # Security telemetry must never break checkout/login if the DB is unavailable.
        pass


def _key(prefix, request, identity=""):
    actor = str(getattr(getattr(request, "user", None), "pk", "")) if getattr(getattr(request, "user", None), "is_authenticated", False) else ""
    raw = f"{prefix}|{ip_hash(request)}|{actor}|{identity}".encode("utf-8")
    return "avan-sec:" + hashlib.sha256(raw).hexdigest()


def hit_limit(request, *, bucket, limit, window_seconds, identity=""):
    key = _key(bucket, request, identity)
    try:
        added = cache.add(key, 1, timeout=window_seconds)
        if added:
            return False, 1
        try:
            count = cache.incr(key)
        except ValueError:
            cache.set(key, 1, timeout=window_seconds)
            count = 1
        return count > limit, count
    except Exception:
        # Fail open if the auxiliary cache is unavailable. Core commerce stays operational.
        return False, 0


LOGIN_WINDOW_SECONDS = int(os.environ.get("AVAN_LOGIN_WINDOW_SECONDS", "900"))
LOGIN_FAILURE_LIMIT = int(os.environ.get("AVAN_LOGIN_FAILURE_LIMIT", "7"))


def login_blocked(request, identifier):
    key = _key("login-fail", request, (identifier or "").strip().lower()[:180])
    try:
        count = int(cache.get(key, 0) or 0)
    except Exception:
        count = 0
    return count >= LOGIN_FAILURE_LIMIT


def record_login_failure(request, identifier):
    blocked, count = hit_limit(
        request,
        bucket="login-fail",
        limit=LOGIN_FAILURE_LIMIT,
        window_seconds=LOGIN_WINDOW_SECONDS,
        identity=(identifier or "").strip().lower()[:180],
    )
    _event(
        "login_failed",
        request,
        severity=SecurityEvent.Severity.HIGH if blocked else SecurityEvent.Severity.WARNING,
        attempt_count=count,
    )
    return blocked


def clear_login_failures(request, identifier):
    key = _key("login-fail", request, (identifier or "").strip().lower()[:180])
    try:
        cache.delete(key)
    except Exception:
        pass
    _event("login_success", request)


def validate_uploaded_image(upload, *, max_bytes=12 * 1024 * 1024, max_width=10000, max_height=10000):
    """Validate image bytes, not only filename/MIME headers."""
    if not upload:
        raise ValidationError("Image is required.")
    if upload.size > max_bytes:
        raise ValidationError(f"Image is larger than {max_bytes // (1024 * 1024)} MB.")

    original_position = None
    try:
        if hasattr(upload, "tell"):
            original_position = upload.tell()
        raw = upload.read()
        upload.seek(0)
        with Image.open(io.BytesIO(raw)) as img:
            fmt = (img.format or "").upper()
            if fmt not in {"PNG", "JPEG", "WEBP"}:
                raise ValidationError("Use a real PNG, JPEG or WebP image.")
            width, height = img.size
            if width <= 0 or height <= 0 or width > max_width or height > max_height:
                raise ValidationError("Image dimensions are not allowed.")
            if width * height > MAX_IMAGE_PIXELS:
                raise ValidationError("Image has too many pixels.")
            img.verify()
    except Image.DecompressionBombError as exc:
        raise ValidationError("Image is too large to process safely.") from exc
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError("The uploaded file is not a valid image.") from exc
    finally:
        try:
            upload.seek(original_position or 0)
        except Exception:
            pass
    return upload
