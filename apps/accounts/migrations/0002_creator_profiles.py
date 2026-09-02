from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="avatar",
            field=models.ImageField(blank=True, null=True, upload_to="avatars/%Y/%m/"),
        ),
        migrations.AddField(
            model_name="user",
            name="bio",
            field=models.CharField(blank=True, max_length=280),
        ),
        migrations.CreateModel(
            name="CreatorFollow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="creator_followers",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "follower",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="following_creators",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="creatorfollow",
            constraint=models.UniqueConstraint(
                fields=("follower", "creator"),
                name="uniq_creator_follow",
            ),
        ),
        migrations.AddConstraint(
            model_name="creatorfollow",
            constraint=models.CheckConstraint(
                condition=~models.Q(follower=models.F("creator")),
                name="prevent_self_follow",
            ),
        ),
    ]
