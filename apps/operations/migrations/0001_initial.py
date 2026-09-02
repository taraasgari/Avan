import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalog", "0001_initial"),
        ("orders", "0003_rename_orders_stoc_variant_8cbd38_idx_orders_stoc_variant_9d0851_idx"),
    ]

    operations = [
        migrations.CreateModel(
            name="ShippingMethod",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=50, unique=True)),
                ("name_en", models.CharField(max_length=100)),
                ("name_fa", models.CharField(max_length=100)),
                ("base_price", models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ("estimated_days_min", models.PositiveSmallIntegerField(default=1)),
                ("estimated_days_max", models.PositiveSmallIntegerField(default=3)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
            ],
            options={"ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="Supplier",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=140)),
                ("contact_name", models.CharField(blank=True, max_length=120)),
                ("phone", models.CharField(blank=True, max_length=30)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("notes", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Address",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(default="Home", max_length=60)),
                ("recipient_name", models.CharField(max_length=120)),
                ("phone", models.CharField(max_length=30)),
                ("province", models.CharField(max_length=80)),
                ("city", models.CharField(max_length=80)),
                ("address", models.TextField()),
                ("postal_code", models.CharField(blank=True, max_length=30)),
                ("is_default", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_addresses", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-is_default", "-updated_at"]},
        ),
        migrations.CreateModel(
            name="InventoryMovement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("restock", "Restock"), ("adjustment", "Manual adjustment"), ("return", "Customer return"), ("production", "Production received"), ("damage", "Damage / write-off")], max_length=20)),
                ("delta", models.IntegerField()),
                ("stock_before", models.PositiveIntegerField()),
                ("stock_after", models.PositiveIntegerField()),
                ("note", models.CharField(blank=True, max_length=240)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="inventory_movements", to=settings.AUTH_USER_MODEL)),
                ("order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="inventory_movements", to="orders.order")),
                ("variant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="inventory_movements", to="catalog.productvariant")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ProductionBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reference", models.CharField(max_length=80, unique=True)),
                ("status", models.CharField(choices=[("planned", "Planned"), ("in_progress", "In progress"), ("ready", "Ready"), ("received", "Received into stock"), ("cancelled", "Cancelled")], default="planned", max_length=20)),
                ("planned_quantity", models.PositiveIntegerField(default=0)),
                ("completed_quantity", models.PositiveIntegerField(default=0)),
                ("notes", models.TextField(blank=True)),
                ("expected_at", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="production_batches", to="catalog.product")),
                ("supplier", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="production_batches", to="operations.supplier")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ReturnRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.CharField(choices=[("size", "Size / fit issue"), ("damaged", "Damaged item"), ("wrong_item", "Wrong item"), ("quality", "Quality issue"), ("other", "Other")], max_length=24)),
                ("status", models.CharField(choices=[("requested", "Requested"), ("approved", "Approved"), ("rejected", "Rejected"), ("received", "Item received"), ("refund_pending", "Refund pending"), ("refunded", "Refunded"), ("closed", "Closed")], default="requested", max_length=24)),
                ("customer_note", models.TextField(blank=True)),
                ("owner_note", models.TextField(blank=True)),
                ("refund_amount", models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="return_requests", to="orders.order")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="return_requests", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Shipment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("packing", "Packing"), ("ready", "Ready to ship"), ("shipped", "Shipped"), ("delivered", "Delivered"), ("returned", "Returned")], default="pending", max_length=16)),
                ("carrier_name", models.CharField(blank=True, max_length=100)),
                ("tracking_code", models.CharField(blank=True, db_index=True, max_length=120)),
                ("owner_note", models.TextField(blank=True)),
                ("shipped_at", models.DateTimeField(blank=True, null=True)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("method", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="shipments", to="operations.shippingmethod")),
                ("order", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="shipment", to="orders.order")),
            ],
        ),
    ]
