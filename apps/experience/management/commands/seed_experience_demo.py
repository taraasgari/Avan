from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.catalog.models import Product
from apps.designs.models import Design
from apps.experience.models import Challenge, Drop, DropItem


class Command(BaseCommand):
    help = "Create safe AVAN demo Drop and Challenge data."

    def handle(self, *args, **options):
        now = timezone.now()

        drop, _ = Drop.objects.update_or_create(
            slug="red-district",
            defaults={
                "title": "RED DISTRICT",
                "subtitle": "DROP 001 / LIMITED AVAN RELEASE",
                "description": "A demo curated release for testing the AVAN Drops experience.",
                "status": Drop.Status.PUBLISHED,
                "starts_at": now - timedelta(days=1),
                "ends_at": now + timedelta(days=30),
                "is_featured": True,
            },
        )

        product = Product.objects.filter(is_active=True).order_by("id").first()
        if product and not drop.items.filter(product=product).exists():
            DropItem.objects.create(drop=drop, product=product, label="DROP 001", sort_order=10)

        design = (
            Design.objects.filter(
                status=Design.Status.PUBLISHED,
                visibility=Design.Visibility.PUBLIC,
            )
            .order_by("-published_at")
            .first()
        )
        if design and not drop.items.filter(design=design).exists():
            DropItem.objects.create(drop=drop, design=design, label="CREATOR PICK", sort_order=20)

        Challenge.objects.update_or_create(
            slug="red-signal",
            defaults={
                "title": "RED SIGNAL",
                "prompt": "Create an AVAN design where red is the dominant visual signal.",
                "description": "Use typography, uploaded artwork or layering. The design must be published publicly before submission.",
                "status": Challenge.Status.PUBLISHED,
                "starts_at": now - timedelta(hours=1),
                "ends_at": now + timedelta(days=14),
                "reward_points": 250,
            },
        )

        self.stdout.write(self.style.SUCCESS("AVAN demo Drop and Challenge are ready."))
