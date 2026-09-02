# Generated for AVAN Stage 10.
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cart", "0002_design_customization"),
        ("coupons", "0002_couponredemption"),
        ("operations", "0001_initial"),
        ("orders", "0002_design_snapshot"),
        ("payments", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="CommerceSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("payment_provider", models.CharField(default="dev", max_length=50)),
                ("free_shipping_threshold", models.DecimalField(blank=True, decimal_places=0, max_digits=12, null=True)),
                ("abandoned_cart_hours", models.PositiveSmallIntegerField(default=24)),
                ("pending_payment_timeout_minutes", models.PositiveSmallIntegerField(default=30)),
                ("auto_detect_abandoned_carts", models.BooleanField(default=True)),
                ("auto_cancel_expired_orders", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Campaign",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("name", models.CharField(max_length=140)),
                ("headline_en", models.CharField(blank=True, max_length=180)),
                ("headline_fa", models.CharField(blank=True, max_length=180)),
                ("starts_at", models.DateTimeField(blank=True, null=True)),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=False)),
                ("priority", models.PositiveIntegerField(default=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("coupon", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="campaigns", to="coupons.coupon")),
            ],
            options={"ordering": ["priority", "-created_at"]},
        ),
        migrations.CreateModel(
            name="ShippingRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("province", models.CharField(blank=True, help_text="Blank means every province.", max_length=80)),
                ("city", models.CharField(blank=True, help_text="Blank means every city.", max_length=80)),
                ("minimum_subtotal", models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ("maximum_subtotal", models.DecimalField(blank=True, decimal_places=0, max_digits=12, null=True)),
                ("price_override", models.DecimalField(blank=True, decimal_places=0, max_digits=12, null=True)),
                ("free_over", models.DecimalField(blank=True, decimal_places=0, max_digits=12, null=True)),
                ("priority", models.PositiveIntegerField(default=100)),
                ("is_active", models.BooleanField(default=True)),
                ("method", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="commerce_rules", to="operations.shippingmethod")),
            ],
            options={"ordering": ["priority", "id"]},
        ),
        migrations.CreateModel(
            name="AbandonedCartEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("detected", "Detected"), ("recovered", "Recovered"), ("dismissed", "Dismissed")], default="detected", max_length=16)),
                ("item_count", models.PositiveIntegerField(default=0)),
                ("value_snapshot", models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ("detected_at", models.DateTimeField(auto_now_add=True)),
                ("recovered_at", models.DateTimeField(blank=True, null=True)),
                ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                ("cart", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="abandoned_event", to="cart.cart")),
            ],
            options={"ordering": ["-detected_at"]},
        ),
        migrations.CreateModel(
            name="Refund",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("idempotency_key", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("amount", models.DecimalField(decimal_places=0, max_digits=12)),
                ("status", models.CharField(choices=[("requested", "Requested"), ("approved", "Approved"), ("processing", "Processing"), ("succeeded", "Succeeded"), ("failed", "Failed"), ("cancelled", "Cancelled")], default="requested", max_length=16)),
                ("provider", models.CharField(blank=True, max_length=50)),
                ("external_reference", models.CharField(blank=True, max_length=180)),
                ("reason", models.CharField(blank=True, max_length=240)),
                ("owner_note", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="approved_refunds", to=settings.AUTH_USER_MODEL)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="refunds", to="orders.order")),
                ("payment_attempt", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="refunds", to="payments.paymentattempt")),
                ("requested_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="requested_refunds", to=settings.AUTH_USER_MODEL)),
                ("return_request", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="refunds", to="operations.returnrequest")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="FulfillmentEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event", models.CharField(max_length=80)),
                ("from_status", models.CharField(blank=True, max_length=40)),
                ("to_status", models.CharField(blank=True, max_length=40)),
                ("note", models.CharField(blank=True, max_length=240)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="fulfillment_events", to=settings.AUTH_USER_MODEL)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fulfillment_events", to="orders.order")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
