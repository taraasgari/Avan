from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("coupons", "0001_initial"),
        ("orders", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="CouponRedemption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("redeemed_at", models.DateTimeField(auto_now_add=True)),
                ("coupon", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="redemptions", to="coupons.coupon")),
                ("order", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="coupon_redemption", to="orders.order")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="coupon_redemptions", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
