import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_alter_user_options_alter_user_groups_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SupportTicket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reference", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("category", models.CharField(choices=[("order", "Order"), ("product", "Product"), ("payment", "Payment"), ("return", "Return / Refund"), ("design", "Design Studio"), ("account", "Account"), ("other", "Other")], default="other", max_length=24)),
                ("subject", models.CharField(max_length=180)),
                ("order_number", models.CharField(blank=True, max_length=80)),
                ("status", models.CharField(choices=[("open", "Open"), ("waiting_support", "Waiting for support"), ("waiting_user", "Waiting for user"), ("closed", "Closed")], default="waiting_support", max_length=24)),
                ("priority", models.CharField(choices=[("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")], default="normal", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("last_message_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="support_tickets", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-last_message_at", "-id"]},
        ),
        migrations.CreateModel(
            name="SupportMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField(max_length=5000)),
                ("is_staff_reply", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("sender", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="support_messages", to=settings.AUTH_USER_MODEL)),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="accounts.supportticket")),
            ],
            options={"ordering": ["created_at", "id"]},
        ),
        migrations.AddIndex(
            model_name="supportticket",
            index=models.Index(fields=["status", "-last_message_at"], name="acct_support_status_idx"),
        ),
        migrations.AddIndex(
            model_name="supportticket",
            index=models.Index(fields=["user", "-last_message_at"], name="acct_support_user_idx"),
        ),
    ]
