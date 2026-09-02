import os


def _bool(name, default="0"):
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def apply_launch_settings(namespace):
    """Stage 13 operational hardening.

    Defaults stay development-friendly. Production-only behavior is driven by
    environment variables so localhost remains usable.
    """
    databases = namespace.get("DATABASES", {})
    default_db = databases.get("default", {})
    default_db["CONN_HEALTH_CHECKS"] = True
    default_db["CONN_MAX_AGE"] = int(os.environ.get("AVAN_DB_CONN_MAX_AGE", "60"))

    namespace["DATA_UPLOAD_MAX_MEMORY_SIZE"] = int(os.environ.get("AVAN_MAX_REQUEST_BYTES", str(24 * 1024 * 1024)))
    namespace["FILE_UPLOAD_MAX_MEMORY_SIZE"] = int(os.environ.get("AVAN_FILE_MEMORY_BYTES", str(4 * 1024 * 1024)))
    namespace["SESSION_COOKIE_NAME"] = os.environ.get("AVAN_SESSION_COOKIE_NAME", "avan_sessionid")
    namespace["CSRF_COOKIE_NAME"] = os.environ.get("AVAN_CSRF_COOKIE_NAME", "avan_csrftoken")
    namespace["SECURE_CROSS_ORIGIN_OPENER_POLICY"] = "same-origin"

    # Hashed static asset names are ideal in production, but keeping this opt-in
    # avoids disrupting local development before collectstatic has run.
    if _bool("AVAN_MANIFEST_STATIC", "0"):
        namespace["STORAGES"] = {
            "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
        }

    namespace["LOGGING"] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {"()": "apps.launchops.logging.JsonFormatter"},
            "plain": {"format": "[{levelname}] {name}: {message}", "style": "{"},
        },
        "handlers": {
            "console_json": {"class": "logging.StreamHandler", "formatter": "json"},
            "console_plain": {"class": "logging.StreamHandler", "formatter": "plain"},
        },
        "root": {
            "handlers": ["console_json" if _bool("AVAN_JSON_LOGS", "0") else "console_plain"],
            "level": os.environ.get("AVAN_LOG_LEVEL", "INFO"),
        },
        "loggers": {
            "django.request": {
                "handlers": ["console_json" if _bool("AVAN_JSON_LOGS", "0") else "console_plain"],
                "level": "WARNING",
                "propagate": False,
            },
            "avan.request": {
                "handlers": ["console_json" if _bool("AVAN_JSON_LOGS", "0") else "console_plain"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
