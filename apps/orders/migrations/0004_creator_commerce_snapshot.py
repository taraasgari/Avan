from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0003_rename_orders_stoc_variant_8cbd38_idx_orders_stoc_variant_9d0851_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="creator_earning_amount",
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="creator_id_snapshot",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="design_fee",
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="garment_unit_price",
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="platform_commission_amount",
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="platform_commission_percent",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
    ]
