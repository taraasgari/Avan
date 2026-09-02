import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("designs", "0004_design_sale_price"),
        ("orders", "0004_creator_commerce_snapshot"),
    ]

    operations = [
        migrations.CreateModel(
            name="MarketplaceSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("commission_percent", models.DecimalField(decimal_places=2, default=0, help_text="AVAN commission from the creator design fee. Set this before launch.", max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ("minimum_payout_amount", models.DecimalField(decimal_places=0, default=0, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ("points_redemption_cost", models.PositiveIntegerField(default=0, help_text="AVAN Points required for one reward coupon. 0 disables redemption.")),
                ("points_coupon_value", models.DecimalField(decimal_places=0, default=0, help_text="Fixed Toman value of the coupon created from points.", max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ("points_coupon_minimum_subtotal", models.DecimalField(decimal_places=0, default=0, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Marketplace settings", "verbose_name_plural": "Marketplace settings"},
        ),
        migrations.CreateModel(
            name="CreatorWallet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("available_balance", models.DecimalField(decimal_places=0, default=0, max_digits=14)),
                ("pending_payout", models.DecimalField(decimal_places=0, default=0, max_digits=14)),
                ("total_earned", models.DecimalField(decimal_places=0, default=0, max_digits=14)),
                ("total_paid", models.DecimalField(decimal_places=0, default=0, max_digits=14)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("creator", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="creator_wallet", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="PayoutRequest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("amount", models.DecimalField(decimal_places=0, max_digits=14, validators=[django.core.validators.MinValueValidator(1)])),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("paid", "Paid"), ("rejected", "Rejected")], default="pending", max_length=16)),
                ("creator_note", models.CharField(blank=True, max_length=240)),
                ("admin_note", models.CharField(blank=True, max_length=240)),
                ("requested_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("creator", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payout_requests", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-requested_at"]},
        ),
        migrations.CreateModel(
            name="CreatorEarning",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("design_id_snapshot", models.UUIDField(blank=True, null=True)),
                ("gross_design_fee", models.DecimalField(decimal_places=0, max_digits=12)),
                ("platform_commission", models.DecimalField(decimal_places=0, max_digits=12)),
                ("creator_amount", models.DecimalField(decimal_places=0, max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("creator", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="creator_earnings", to=settings.AUTH_USER_MODEL)),
                ("design", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="creator_earnings", to="designs.design")),
                ("order_item", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="creator_earning", to="orders.orderitem")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(model_name="creatorwallet", constraint=models.CheckConstraint(condition=models.Q(("available_balance__gte", 0)), name="creator_wallet_available_gte_0")),
        migrations.AddConstraint(model_name="creatorwallet", constraint=models.CheckConstraint(condition=models.Q(("pending_payout__gte", 0)), name="creator_wallet_pending_gte_0")),
        migrations.AddConstraint(model_name="creatorwallet", constraint=models.CheckConstraint(condition=models.Q(("total_earned__gte", 0)), name="creator_wallet_earned_gte_0")),
        migrations.AddConstraint(model_name="creatorwallet", constraint=models.CheckConstraint(condition=models.Q(("total_paid__gte", 0)), name="creator_wallet_paid_gte_0")),
    ]
