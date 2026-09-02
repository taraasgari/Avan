from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("coupons", "0002_couponredemption"),
    ]

    operations = [
        migrations.AddField(
            model_name="coupon",
            name="assigned_user",
            field=models.ForeignKey(
                blank=True,
                help_text="Optional account lock. Used by AVAN Points reward coupons.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="assigned_coupons",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
