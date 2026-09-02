import os
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache
from django.db import connections


@dataclass
class LaunchCheck:
    key: str
    label: str
    ok: bool
    detail: str
    critical: bool = True


def _secret_is_strong():
    secret = str(settings.SECRET_KEY or "")
    return len(secret) >= 50 and len(set(secret)) >= 10 and not secret.startswith("django-insecure-") and secret != "unsafe-dev-key"


def database_ready():
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            return cursor.fetchone()[0] == 1
    except Exception:
        return False


def cache_ready():
    try:
        key = "avan:launch:health"
        cache.set(key, "ok", timeout=10)
        return cache.get(key) == "ok"
    except Exception:
        return False


def collect_launch_checks(include_dependencies=True):
    allowed = [host for host in settings.ALLOWED_HOSTS if host]
    trusted_origins = list(getattr(settings, "CSRF_TRUSTED_ORIGINS", []))
    checks = [
        LaunchCheck("debug", "DEBUG disabled", not settings.DEBUG, f"DEBUG={settings.DEBUG}"),
        LaunchCheck("secret", "Strong DJANGO_SECRET_KEY", _secret_is_strong(), "50+ chars, varied and not a development key"),
        LaunchCheck("hosts", "ALLOWED_HOSTS restricted", bool(allowed) and "*" not in allowed, ", ".join(allowed) or "empty"),
        LaunchCheck("ssl_redirect", "HTTPS redirect enabled", bool(getattr(settings, "SECURE_SSL_REDIRECT", False)), f"SECURE_SSL_REDIRECT={getattr(settings, 'SECURE_SSL_REDIRECT', False)}"),
        LaunchCheck("session_secure", "Secure session cookie", bool(getattr(settings, "SESSION_COOKIE_SECURE", False)), f"SESSION_COOKIE_SECURE={getattr(settings, 'SESSION_COOKIE_SECURE', False)}"),
        LaunchCheck("csrf_secure", "Secure CSRF cookie", bool(getattr(settings, "CSRF_COOKIE_SECURE", False)), f"CSRF_COOKIE_SECURE={getattr(settings, 'CSRF_COOKIE_SECURE', False)}"),
        LaunchCheck("hsts", "HSTS enabled", int(getattr(settings, "SECURE_HSTS_SECONDS", 0) or 0) >= 86400, f"SECURE_HSTS_SECONDS={getattr(settings, 'SECURE_HSTS_SECONDS', 0)}"),
        LaunchCheck("csp", "CSP enforcement enabled", os.environ.get("AVAN_CSP_ENFORCE", "0") == "1", f"AVAN_CSP_ENFORCE={os.environ.get('AVAN_CSP_ENFORCE', '0')}"),
        LaunchCheck("proxy", "Trusted HTTPS proxy configured", os.environ.get("AVAN_BEHIND_HTTPS_PROXY", "0") == "1", f"AVAN_BEHIND_HTTPS_PROXY={os.environ.get('AVAN_BEHIND_HTTPS_PROXY', '0')}", critical=False),
        LaunchCheck("csrf_origins", "Production CSRF origins use HTTPS", bool(trusted_origins) and all(origin.startswith("https://") for origin in trusted_origins), ", ".join(trusted_origins) or "empty"),
        LaunchCheck("admin_path", "Non-default production admin path", os.environ.get("DJANGO_ADMIN_URL", "admin/").strip("/") not in {"", "admin"}, os.environ.get("DJANGO_ADMIN_URL", "admin/"), critical=False),
        LaunchCheck("metrics_token", "Metrics endpoint token configured", len(os.environ.get("AVAN_METRICS_TOKEN", "")) >= 32, "configured" if os.environ.get("AVAN_METRICS_TOKEN") else "disabled", critical=False),
    ]
    if include_dependencies:
        checks.extend([
            LaunchCheck("database", "Database ready", database_ready(), "SELECT 1"),
            LaunchCheck("cache", "Cache ready", cache_ready(), "cache set/get", critical=False),
        ])
    return checks
