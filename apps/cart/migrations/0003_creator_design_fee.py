from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cart", "0002_design_customization"),
    ]

    operations = [
        migrations.AddField(
            model_name="cartitem",
            name="design_fee",
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12),
        ),
    ]
