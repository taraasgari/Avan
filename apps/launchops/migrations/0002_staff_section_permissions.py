from django.db import migrations, models


def backfill_sections(apps, schema_editor):
    StaffAccess = apps.get_model("launchops", "StaffAccess")
    for access in StaffAccess.objects.all():
        sections = ["dashboard"] if access.can_view_dashboard else []
        if access.can_view_analytics: sections.append("analytics")
        if access.can_manage_catalog: sections += ["products", "catalog"]
        if access.can_manage_inventory: sections += ["inventory", "production"]
        if access.can_manage_orders: sections += ["orders", "operations", "shipping", "returns"]
        if access.can_manage_customers: sections += ["customers", "support"]
        if access.can_manage_designs: sections += ["designs", "creators", "moderation"]
        if access.can_manage_marketing: sections += ["play", "marketing", "growth"]
        if access.can_manage_finance: sections += ["finance", "commerce"]
        if access.can_manage_content: sections.append("content")
        if access.can_manage_reports: sections.append("reports")
        if access.can_manage_security: sections.append("security")
        if access.can_manage_settings: sections.append("settings")
        access.section_permissions = sorted(set(sections))
        access.save(update_fields=["section_permissions"])


class Migration(migrations.Migration):
    dependencies = [("launchops", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="staffaccess",
            name="section_permissions",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(backfill_sections, migrations.RunPython.noop),
    ]
