from django.apps import AppConfig


class LaunchOpsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.launchops"
    verbose_name = "AVAN Launch Operations"

    def ready(self):
        # Register deployment checks when Django starts.
        from . import checks  # noqa: F401
