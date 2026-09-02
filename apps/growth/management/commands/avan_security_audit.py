import os

from django.conf import settings
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = "Run Django deploy checks plus AVAN-specific security configuration checks."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Django deployment checks"))
        try:
            call_command("check", "--deploy")
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"Django deploy check reported issues: {exc}"))

        checks = [
            (not settings.DEBUG, "DEBUG is disabled"),
            (settings.SECRET_KEY != "unsafe-dev-key" and len(settings.SECRET_KEY) >= 40, "strong DJANGO_SECRET_KEY is configured"),
            (bool(settings.ALLOWED_HOSTS) and "*" not in settings.ALLOWED_HOSTS, "ALLOWED_HOSTS is restricted"),
            (getattr(settings, "SESSION_COOKIE_HTTPONLY", False), "session cookie is HttpOnly"),
            (getattr(settings, "CSRF_COOKIE_HTTPONLY", False), "CSRF cookie is HttpOnly"),
            (getattr(settings, "SESSION_COOKIE_SECURE", False), "session cookie is Secure"),
            (getattr(settings, "CSRF_COOKIE_SECURE", False), "CSRF cookie is Secure"),
            (getattr(settings, "SECURE_HSTS_SECONDS", 0) > 0, "HSTS is enabled"),
            (os.environ.get("AVAN_CSP_ENFORCE", "0") == "1", "CSP enforcement is enabled"),
        ]
        self.stdout.write(self.style.MIGRATE_HEADING("AVAN production checklist"))
        failed = 0
        for ok, label in checks:
            if ok:
                self.stdout.write(self.style.SUCCESS(f"PASS  {label}"))
            else:
                failed += 1
                self.stdout.write(self.style.WARNING(f"WARN  {label}"))
        if failed:
            self.stdout.write(self.style.WARNING(f"{failed} production-hardening item(s) still need attention."))
        else:
            self.stdout.write(self.style.SUCCESS("All AVAN production security switches are enabled."))
