import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cart", "0001_initial"),
        ("catalog", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("idempotency_key", models.UUIDField(default=uuid.uuid4, unique=True)),
                ("status", models.CharField(choices=[("pending_payment", "Pending payment"), ("paid", "Paid"), ("processing", "Processing"), ("shipped", "Shipped"), ("delivered", "Delivered"), ("cancelled", "Cancelled"), ("needs_review", "Needs review")], default="pending_payment", max_length=24)),
                ("subtotal", models.DecimalField(decimal_places=0, max_digits=12)),
                ("discount_amount", models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ("shipping_amount", models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ("total_amount", models.DecimalField(decimal_places=0, max_digits=12)),
                ("customer_name", models.CharField(max_length=120)),
                ("phone", models.CharField(max_length=30)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("province", models.CharField(max_length=80)),
                ("city", models.CharField(max_length=80)),
                ("address", models.TextField()),
                ("postal_code", models.CharField(blank=True, max_length=30)),
                ("customer_note", models.TextField(blank=True)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("cart", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="orders", to="cart.cart")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="orders", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_name", models.CharField(max_length=180)),
                ("sku", models.CharField(max_length=80)),
                ("color_name", models.CharField(max_length=60)),
                ("size_name", models.CharField(max_length=30)),
                ("unit_price", models.DecimalField(decimal_places=0, max_digits=12)),
                ("quantity", models.PositiveIntegerField()),
                ("line_total", models.DecimalField(decimal_places=0, max_digits=12)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="orders.order")),
                ("variant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_items", to="catalog.productvariant")),
            ],
        ),
        migrations.CreateModel(
            name="StockReservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField()),
                ("status", models.CharField(choices=[("active", "Active"), ("consumed", "Consumed"), ("released", "Released")], default="active", max_length=12)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reservations", to="orders.order")),
                ("variant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reservations", to="catalog.productvariant")),
            ],
        ),
        migrations.AddIndex(
            model_name="stockreservation",
            index=models.Index(fields=["variant", "status", "expires_at"], name="orders_stoc_variant_8cbd38_idx"),
        ),
    ]
