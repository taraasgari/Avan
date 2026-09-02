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
            name="DesignAsset",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("image", models.ImageField(upload_to="design-assets/%Y/%m/")),
                ("original_name", models.CharField(blank=True, max_length=255)),
                ("mime_type", models.CharField(blank=True, max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="design_assets", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="GarmentMockup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("side", models.CharField(choices=[("front", "Front"), ("back", "Back")], max_length=10)),
                ("image", models.ImageField(upload_to="garment-mockups/%Y/%m/")),
                ("print_x", models.DecimalField(decimal_places=2, default=25, max_digits=5)),
                ("print_y", models.DecimalField(decimal_places=2, default=22, max_digits=5)),
                ("print_width", models.DecimalField(decimal_places=2, default=50, max_digits=5)),
                ("print_height", models.DecimalField(decimal_places=2, default=55, max_digits=5)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("color", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="design_mockups", to="catalog.color")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="design_mockups", to="catalog.product")),
            ],
            options={"ordering": ["product_id", "color_id", "side", "id"]},
        ),
        migrations.CreateModel(
            name="Design",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(default="Untitled Design", max_length=120)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published")], default="draft", max_length=16)),
                ("visibility", models.CharField(choices=[("private", "Private"), ("public", "Public")], default="private", max_length=16)),
                ("allow_remix", models.BooleanField(default=False)),
                ("design_data", models.JSONField(blank=True, default=dict)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("base_color", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="customer_designs", to="catalog.color")),
                ("base_product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="customer_designs", to="catalog.product")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="designs", to=settings.AUTH_USER_MODEL)),
                ("parent_design", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="remixes", to="designs.design")),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.AddIndex(
            model_name="design",
            index=models.Index(fields=["status", "visibility", "-published_at"], name="designs_des_status_5e1448_idx"),
        ),
    ]
