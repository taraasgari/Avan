from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import Client


class Command(BaseCommand):
    help = "Run a non-destructive smoke test against critical AVAN public endpoints using Django's request stack."

    def add_arguments(self, parser):
        parser.add_argument("--host", default="", help="Host header to test. Defaults to the first ALLOWED_HOSTS entry.")

    def handle(self, *args, **options):
        host = options["host"] or next((h for h in settings.ALLOWED_HOSTS if h and h != "*"), "localhost")
        secure = bool(getattr(settings, "SECURE_SSL_REDIRECT", False))
        client = Client(HTTP_HOST=host)
        endpoints = [
            ("liveness", "/_health/live/", {200}),
            ("readiness", "/_health/ready/", {200}),
            ("home", "/", {200}),
            ("shop", "/shop/", {200}),
            ("sitemap", "/sitemap.xml", {200}),
            ("robots", "/robots.txt", {200}),
            ("service worker", "/sw.js", {200}),
        ]

        failures = []
        for label, path, expected in endpoints:
            response = client.get(path, secure=secure, follow=False)
            if response.status_code in expected:
                self.stdout.write(self.style.SUCCESS(f"PASS  {label:<16} {path} -> {response.status_code}"))
            else:
                failures.append((label, path, response.status_code))
                self.stdout.write(self.style.ERROR(f"FAIL  {label:<16} {path} -> {response.status_code}"))

        if failures:
            raise CommandError(f"{len(failures)} AVAN smoke test(s) failed.")
        self.stdout.write(self.style.SUCCESS("AVAN smoke test passed."))
