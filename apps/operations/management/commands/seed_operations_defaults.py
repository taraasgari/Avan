from django.core.management.base import BaseCommand

from apps.operations.models import ShippingMethod


class Command(BaseCommand):
    help = "Create safe zero-price default shipping methods. Owner should set real prices before production."

    def handle(self, *args, **options):
        defaults = [
            ("standard", "Standard shipping", "ارسال استاندارد", 1, 5),
            ("express", "Express shipping", "ارسال سریع", 1, 3),
        ]
        for sort_order, (code, en, fa, min_days, max_days) in enumerate(defaults):
            ShippingMethod.objects.get_or_create(
                code=code,
                defaults={
                    "name_en": en,
                    "name_fa": fa,
                    "base_price": 0,
                    "estimated_days_min": min_days,
                    "estimated_days_max": max_days,
                    "sort_order": sort_order,
                    "is_active": True,
                },
            )
        self.stdout.write(self.style.SUCCESS("AVAN shipping methods are ready with price=0. Set real prices in Owner/Admin before production."))
