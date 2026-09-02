from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Coupon",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=40, unique=True)),
                ("discount_type", models.CharField(choices=[("percent", "Percent"), ("fixed", "Fixed")], max_length=10)),
                ("value", models.DecimalField(decimal_places=0, max_digits=12)),
                ("minimum_subtotal", models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ("maximum_discount", models.DecimalField(blank=True, decimal_places=0, max_digits=12, null=True)),
                ("starts_at", models.DateTimeField(blank=True, null=True)),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("usage_limit", models.PositiveIntegerField(blank=True, null=True)),
                ("usage_limit_per_user", models.PositiveIntegerField(default=1)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
