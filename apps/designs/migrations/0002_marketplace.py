from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("designs", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="design",
            name="is_for_sale",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="DesignLike",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("design", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="likes", to="designs.design")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="design_likes", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="DesignSave",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("design", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saves", to="designs.design")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_designs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="designlike",
            constraint=models.UniqueConstraint(fields=("user", "design"), name="uniq_design_like"),
        ),
        migrations.AddConstraint(
            model_name="designsave",
            constraint=models.UniqueConstraint(fields=("user", "design"), name="uniq_design_save"),
        ),
    ]
