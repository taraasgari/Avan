from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.orders.models import StockReservation


class Command(BaseCommand):
    help = "Release expired stock reservations. Correctness does not depend on this command; it is cleanup."

    def handle(self, *args, **options):
        count = StockReservation.objects.filter(
            status=StockReservation.Status.ACTIVE,
            expires_at__lte=timezone.now(),
        ).update(status=StockReservation.Status.RELEASED)
        self.stdout.write(self.style.SUCCESS(f"Released {count} expired reservation(s)."))
