from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0005_tracking_codes"),
        ("accounts", "0004_support_tickets"),
    ]
    operations = [
        migrations.AddField(
            model_name="supportticket",
            name="order",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="support_tickets", to="orders.order"),
        ),
    ]
