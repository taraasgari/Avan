from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("marketplace", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="marketplacesettings",
            name="creator_pricing_enabled",
            field=models.BooleanField(
                default=False,
                help_text="When off, published designs can still be worn/bought but no separate creator design fee is charged.",
            ),
        ),
    ]
