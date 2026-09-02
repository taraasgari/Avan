from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.commerce.models import CommerceSettings
from apps.commerce.services import detect_abandoned_carts
from apps.orders.models import Order, StockReservation
from apps.orders.services import release_order


class Command(BaseCommand):
    help = "Run safe recurring AVAN commerce maintenance."

    def handle(self, *args, **options):
        config = CommerceSettings.load()
        if config.auto_detect_abandoned_carts:
            result = detect_abandoned_carts()
            self.stdout.write(f"Abandoned carts: {result}")

        expired_order_ids = list(
            StockReservation.objects.filter(
                status=StockReservation.Status.ACTIVE,
                expires_at__lte=timezone.now(),
                order__status=Order.Status.PENDING_PAYMENT,
            ).values_list("order_id", flat=True).distinct()
        )
        if config.auto_cancel_expired_orders:
            for order in Order.objects.filter(id__in=expired_order_ids):
                release_order(order)
            self.stdout.write(f"Expired pending orders cancelled: {len(expired_order_ids)}")
        else:
            self.stdout.write(f"Expired pending orders found: {len(expired_order_ids)} (auto-cancel OFF)")
