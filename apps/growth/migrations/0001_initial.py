# Generated for AVAN Stage 12
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SeoRedirect",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("old_path", models.CharField(max_length=500, unique=True)),
                ("new_path", models.CharField(max_length=500)),
                ("is_active", models.BooleanField(default=True)),
                ("hit_count", models.PositiveBigIntegerField(default=0)),
                ("last_hit_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["old_path"]},
        ),
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_updates", models.BooleanField(default=True)),
                ("social_activity", models.BooleanField(default=True)),
                ("rewards", models.BooleanField(default=True)),
                ("product_and_drop_news", models.BooleanField(default=True)),
                ("security_alerts", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="notification_preference", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="SecurityEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(max_length=60)),
                ("severity", models.CharField(choices=[("info", "Info"), ("warning", "Warning"), ("high", "High")], default="info", max_length=12)),
                ("ip_hash", models.CharField(blank=True, max_length=64)),
                ("path", models.CharField(blank=True, max_length=500)),
                ("details", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="security_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="ContentReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("target_type", models.CharField(choices=[("design", "Design"), ("creator", "Creator")], max_length=20)),
                ("target_id", models.CharField(max_length=100)),
                ("target_label", models.CharField(blank=True, max_length=220)),
                ("reason", models.CharField(choices=[("spam", "Spam"), ("copyright", "Copyright"), ("abuse", "Abusive content"), ("misleading", "Misleading"), ("other", "Other")], max_length=30)),
                ("details", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("open", "Open"), ("reviewing", "Reviewing"), ("resolved", "Resolved"), ("dismissed", "Dismissed")], default="open", max_length=20)),
                ("resolution_note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("reporter", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="content_reports", to=settings.AUTH_USER_MODEL)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_content_reports", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.AddIndex(model_name="securityevent", index=models.Index(fields=["kind", "-created_at"], name="growth_secu_kind_395541_idx")),
        migrations.AddIndex(model_name="securityevent", index=models.Index(fields=["severity", "-created_at"], name="growth_secu_severit_e955ef_idx")),
        migrations.AddIndex(model_name="contentreport", index=models.Index(fields=["status", "-created_at"], name="growth_cont_status_1d928a_idx")),
    ]
