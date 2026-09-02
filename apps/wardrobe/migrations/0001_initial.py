# Generated for AVAN Stage 5
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Outfit",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(default="New Outfit", max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="outfits", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="SizePassport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("height_cm", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("weight_kg", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("chest_cm", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("waist_cm", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("hip_cm", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("preferred_fit", models.CharField(choices=[("slim", "Slim"), ("regular", "Regular"), ("relaxed", "Relaxed"), ("oversized", "Oversized")], default="regular", max_length=16)),
                ("notes", models.CharField(blank=True, max_length=240)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("usual_top_size", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="size_passports", to="catalog.size")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="size_passport", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="OutfitItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("position", models.CharField(choices=[("top", "Top"), ("bottom", "Bottom"), ("outerwear", "Outerwear"), ("shoes", "Shoes"), ("accessory", "Accessory"), ("other", "Other")], default="other", max_length=16)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("outfit", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="wardrobe.outfit")),
                ("variant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="outfit_items", to="catalog.productvariant")),
            ],
            options={"ordering": ["sort_order", "id"]},
        ),
        migrations.AddConstraint(
            model_name="outfititem",
            constraint=models.UniqueConstraint(fields=("outfit", "variant"), name="uniq_outfit_variant"),
        ),
    ]
