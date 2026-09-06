from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ("designs", "0005_studio_3d"),
    ]

    operations = [
        migrations.AddField(
            model_name="garmentstudioprofile",
            name="front_reference",
            field=models.ImageField(blank=True, upload_to="studio-garments/front/%Y/%m/"),
        ),
        migrations.AddField(
            model_name="garmentstudioprofile",
            name="back_reference",
            field=models.ImageField(blank=True, upload_to="studio-garments/back/%Y/%m/"),
        ),
        migrations.AddField(
            model_name="garmentstudioprofile",
            name="left_sleeve_reference",
            field=models.ImageField(blank=True, upload_to="studio-garments/left-sleeve/%Y/%m/"),
        ),
        migrations.AddField(
            model_name="garmentstudioprofile",
            name="right_sleeve_reference",
            field=models.ImageField(blank=True, upload_to="studio-garments/right-sleeve/%Y/%m/"),
        ),
        migrations.AddField(
            model_name="garmentstudioprofile",
            name="model_file",
            field=models.FileField(
                blank=True,
                help_text="Optional product-specific 3D garment model. GLB is recommended.",
                upload_to="studio-garments/models/%Y/%m/",
                validators=[django.core.validators.FileExtensionValidator(["glb", "gltf"])],
            ),
        ),
    ]
