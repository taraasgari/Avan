from django.core.management.base import BaseCommand, CommandError

from apps.launchops.status import collect_launch_checks


class Command(BaseCommand):
    help = "Run AVAN production go/no-go checks."

    def add_arguments(self, parser):
        parser.add_argument("--strict", action="store_true", help="Exit non-zero when any critical launch check fails.")

    def handle(self, *args, **options):
        checks = collect_launch_checks(include_dependencies=True)
        failed_critical = []
        for item in checks:
            if item.ok:
                status = self.style.SUCCESS("PASS")
            elif item.critical:
                status = self.style.ERROR("FAIL")
                failed_critical.append(item)
            else:
                status = self.style.WARNING("WARN")
            self.stdout.write(f"{status}  {item.label} — {item.detail}")

        self.stdout.write("")
        if failed_critical:
            self.stdout.write(self.style.ERROR(f"{len(failed_critical)} critical launch check(s) failed."))
            if options["strict"]:
                raise CommandError("AVAN is not production-ready.")
        else:
            self.stdout.write(self.style.SUCCESS("All critical AVAN launch checks passed."))
