from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("designs", "0006_garment_product_assets")]
    operations = [
        migrations.AddField(model_name="garmentstudioprofile", name="neck_label_reference", field=models.ImageField(blank=True, upload_to="studio-garments/neck-label/%Y/%m/")),
        migrations.AddField(model_name="garmentstudioprofile", name="print_zones", field=models.JSONField(blank=True, default=dict, help_text="Per-view printable area percentages.")),
    ]
