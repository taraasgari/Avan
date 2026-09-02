# Generated for AVAN Stage 13.
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
            name="StaffAccess",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("manager", "Manager"), ("catalog", "Catalog / Content"), ("fulfillment", "Warehouse / Fulfillment"), ("support", "Customer Support"), ("marketing", "Marketing / Community"), ("finance", "Finance"), ("security", "Security / Audit"), ("custom", "Custom")], default="custom", max_length=24)),
                ("can_view_dashboard", models.BooleanField(default=True)),
                ("can_view_analytics", models.BooleanField(default=False)),
                ("can_manage_catalog", models.BooleanField(default=False)),
                ("can_manage_inventory", models.BooleanField(default=False)),
                ("can_manage_orders", models.BooleanField(default=False)),
                ("can_manage_customers", models.BooleanField(default=False)),
                ("can_manage_designs", models.BooleanField(default=False)),
                ("can_manage_marketing", models.BooleanField(default=False)),
                ("can_manage_finance", models.BooleanField(default=False)),
                ("can_manage_content", models.BooleanField(default=False)),
                ("can_manage_reports", models.BooleanField(default=False)),
                ("can_manage_security", models.BooleanField(default=False)),
                ("can_manage_settings", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="updated_staff_access_records", to=settings.AUTH_USER_MODEL)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="avan_staff_access", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Staff access", "verbose_name_plural": "Staff access", "ordering": ["user__username"]},
        ),
        migrations.CreateModel(
            name="OwnerAuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=80)),
                ("path", models.CharField(max_length=500)),
                ("method", models.CharField(max_length=10)),
                ("status_code", models.PositiveSmallIntegerField(default=200)),
                ("request_id", models.CharField(blank=True, max_length=64)),
                ("target", models.CharField(blank=True, max_length=180)),
                ("details", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="owner_audit_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at", "-id"],
                "indexes": [
                    models.Index(fields=["-created_at"], name="launch_audit_created_idx"),
                    models.Index(fields=["actor", "-created_at"], name="launch_audit_actor_idx"),
                    models.Index(fields=["action", "-created_at"], name="launch_audit_action_idx"),
                ],
            },
        ),
    ]
