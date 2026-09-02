from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=140, unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
            ],
            options={"ordering": ["sort_order", "name"]},
        ),
        migrations.CreateModel(
            name="Color",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=60)),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("hex_code", models.CharField(blank=True, max_length=7)),
            ],
        ),
        migrations.CreateModel(
            name="Size",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=30)),
                ("sort_order", models.PositiveIntegerField(default=0)),
            ],
            options={"ordering": ["sort_order", "name"]},
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=180)),
                ("slug", models.SlugField(max_length=200, unique=True)),
                ("description", models.TextField(blank=True)),
                ("base_price", models.DecimalField(decimal_places=0, max_digits=12)),
                ("product_type", models.CharField(choices=[("ready", "Ready design"), ("customizable", "Customizable")], default="ready", max_length=20)),
                ("is_active", models.BooleanField(default=True)),
                ("is_featured", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="products", to="catalog.category")),
            ],
        ),
        migrations.CreateModel(
            name="ProductImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="products/%Y/%m/")),
                ("alt_text", models.CharField(blank=True, max_length=180)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="catalog.product")),
            ],
            options={"ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="ProductVariant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sku", models.CharField(max_length=80, unique=True)),
                ("stock", models.PositiveIntegerField(default=0)),
                ("price_override", models.DecimalField(blank=True, decimal_places=0, max_digits=12, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("color", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="variants", to="catalog.color")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="variants", to="catalog.product")),
                ("size", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="variants", to="catalog.size")),
            ],
        ),
        migrations.AddConstraint(
            model_name="productvariant",
            constraint=models.UniqueConstraint(fields=("product", "color", "size"), name="uniq_product_color_size"),
        ),
    ]
