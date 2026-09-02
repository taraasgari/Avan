from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0001_initial"),
        ("cart", "0002_design_customization"),
    ]

    operations = [
        migrations.AddField(model_name="orderitem", name="is_customized", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="orderitem", name="design_id_snapshot", field=models.UUIDField(blank=True, null=True)),
        migrations.AddField(model_name="orderitem", name="design_title", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="orderitem", name="design_owner_name", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="orderitem", name="design_snapshot", field=models.JSONField(blank=True, default=dict)),
    ]
