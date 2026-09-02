import os


def _bool(name, default="0"):
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def apply_security_settings(namespace):
    """Apply hardened settings without breaking localhost development."""
    debug = bool(namespace.get("DEBUG"))

    namespace["SESSION_COOKIE_HTTPONLY"] = True
    namespace["CSRF_COOKIE_HTTPONLY"] = True
    namespace["SESSION_COOKIE_SAMESITE"] = "Lax"
    namespace["CSRF_COOKIE_SAMESITE"] = "Lax"
    namespace["SECURE_CONTENT_TYPE_NOSNIFF"] = True
    namespace["X_FRAME_OPTIONS"] = "DENY"
    namespace["SECURE_REFERRER_POLICY"] = "strict-origin-when-cross-origin"

    # Production TLS switches are environment driven so localhost:8000 does not redirect to HTTPS.
    production_secure = _bool("AVAN_PRODUCTION_SECURE", "0") and not debug
    namespace["SESSION_COOKIE_SECURE"] = production_secure
    namespace["CSRF_COOKIE_SECURE"] = production_secure
    namespace["SECURE_SSL_REDIRECT"] = production_secure
    namespace["SECURE_HSTS_SECONDS"] = int(os.environ.get("AVAN_HSTS_SECONDS", "31536000")) if production_secure else 0
    namespace["SECURE_HSTS_INCLUDE_SUBDOMAINS"] = production_secure
    namespace["SECURE_HSTS_PRELOAD"] = production_secure

    if _bool("AVAN_BEHIND_HTTPS_PROXY", "0"):
        namespace["SECURE_PROXY_SSL_HEADER"] = ("HTTP_X_FORWARDED_PROTO", "https")

    # New passwords use Argon2; Django transparently keeps verifying older PBKDF2 hashes.
    namespace["PASSWORD_HASHERS"] = [
        "django.contrib.auth.hashers.Argon2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
        "django.contrib.auth.hashers.ScryptPasswordHasher",
    ]
