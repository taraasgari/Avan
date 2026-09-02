from django.core.management.base import BaseCommand
from apps.catalog.models import Category, Color, Product, ProductVariant, Size


class Command(BaseCommand):
    help = "Create a small idempotent clothing catalog for local Phase 2 testing."

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(name="T-Shirts", slug="t-shirts")
        black, _ = Color.objects.get_or_create(name="Black", slug="black", defaults={"hex_code": "#111111"})
        white, _ = Color.objects.get_or_create(name="White", slug="white", defaults={"hex_code": "#FFFFFF"})
        sizes = []
        for i, name in enumerate(["M", "L", "XL"], start=1):
            size, _ = Size.objects.get_or_create(name=name, defaults={"sort_order": i})
            sizes.append(size)
        product, _ = Product.objects.get_or_create(
            slug="avan-oversized-tee",
            defaults={
                "name": "AVAN Oversized Tee",
                "category": category,
                "description": "Local demo product for Phase 2 commerce testing.",
                "base_price": 890000,
                "product_type": Product.ProductType.CUSTOMIZABLE,
                "is_active": True,
                "is_featured": True,
            },
        )
        for color in [black, white]:
            for size in sizes:
                ProductVariant.objects.get_or_create(
                    product=product, color=color, size=size,
                    defaults={"sku": f"DEMO-{color.slug.upper()}-{size.name}", "stock": 10},
                )
        self.stdout.write(self.style.SUCCESS("Demo catalog is ready."))
