import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [("orders", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="PaymentAttempt",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("provider", models.CharField(max_length=50)),
                ("amount", models.DecimalField(decimal_places=0, max_digits=12)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("redirected", "Redirected"), ("succeeded", "Succeeded"), ("failed", "Failed"), ("cancelled", "Cancelled"), ("requires_review", "Requires review")], default="pending", max_length=20)),
                ("external_reference", models.CharField(blank=True, max_length=160)),
                ("redirect_url", models.URLField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payment_attempts", to="orders.order")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
