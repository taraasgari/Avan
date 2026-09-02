from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("designs", "0003_rename_designs_des_status_5e1448_idx_designs_des_status_a6b6ae_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name="design",
            name="sale_price",
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12),
        ),
    ]
