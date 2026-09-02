from django.core.management.base import BaseCommand

from apps.catalog.models import Category, Product


class Command(BaseCommand):
    help = "Copy legacy catalog text into missing English fields. Persian content remains manual."

    def handle(self, *args, **options):
        products = 0
        categories = 0
        for product in Product.objects.all().iterator():
            changed = []
            if not product.name_en:
                product.name_en = product.name
                changed.append("name_en")
            if not product.description_en:
                product.description_en = product.description
                changed.append("description_en")
            if not product.seo_title_en:
                product.seo_title_en = product.name_en or product.name
                changed.append("seo_title_en")
            if changed:
                product.save(update_fields=changed)
                products += 1
        for category in Category.objects.all().iterator():
            changed = []
            if not category.name_en:
                category.name_en = category.name
                changed.append("name_en")
            if not category.seo_title_en:
                category.seo_title_en = category.name_en or category.name
                changed.append("seo_title_en")
            if changed:
                category.save(update_fields=changed)
                categories += 1
        self.stdout.write(self.style.SUCCESS(f"Backfilled {products} products and {categories} categories. Persian fields were not auto-translated."))
