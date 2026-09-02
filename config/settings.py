from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


SECRET_KEY = env("DJANGO_SECRET_KEY", "unsafe-dev-key")
DEBUG = env("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = [x.strip() for x in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if x.strip()]
CSRF_TRUSTED_ORIGINS = [x.strip() for x in env("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if x.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.core",
    "apps.accounts",
    "apps.catalog",
    "apps.coupons",
    "apps.cart",
    "apps.orders",
    "apps.wishlist",
    "apps.notifications",
    "apps.payments",
    "apps.designs",
    "apps.experience",
    "apps.wardrobe",
    "apps.marketplace",
    "apps.owner",
    "apps.operations",
    "apps.commerce",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "apps.core.middleware.AvanLocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.brand",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "avan"),
        "USER": env("POSTGRES_USER", "avan"),
        "PASSWORD": env("POSTGRES_PASSWORD", "avan-dev-only"),
        "HOST": env("POSTGRES_HOST", "db"),
        "PORT": env("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "accounts.User"

LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("fa", "فارسی"),
]
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Core commerce never requires Redis. Local memory is the safe default.
if env("ENABLE_REDIS_CACHE", "0") == "1":
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": env("REDIS_URL", "redis://redis:6379/0"),
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient", "IGNORE_EXCEPTIONS": True},
        }
    }
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

CELERY_BROKER_URL = env("CELERY_BROKER_URL", "redis://redis:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", "redis://redis:6379/2")
CELERY_TASK_IGNORE_RESULT = True
CELERY_TASK_ACKS_LATE = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

# Production-safe defaults. HTTPS-specific flags can be enabled at deployment.
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Commerce settings. Keep core checkout independent from Redis/Celery.
ORDER_RESERVATION_MINUTES = int(env("ORDER_RESERVATION_MINUTES", "20"))
DEFAULT_SHIPPING_AMOUNT = int(env("DEFAULT_SHIPPING_AMOUNT", "0"))
