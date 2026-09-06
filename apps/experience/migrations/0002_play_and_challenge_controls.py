from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
        ("experience", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="challenge",
            name="is_enabled",
            field=models.BooleanField(default=True, help_text="Master visibility switch for the public site."),
        ),
        migrations.AddField(
            model_name="challenge",
            name="challenge_type",
            field=models.CharField(default="theme", max_length=32),
        ),
        migrations.AddField(
            model_name="challenge",
            name="garment_product",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="design_challenges",
                to="catalog.product",
            ),
        ),
        migrations.AddField(
            model_name="challenge",
            name="rules",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.CreateModel(
            name="SoloGame",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("game_type", models.CharField(choices=[("runner", "Thread Runner"), ("catch", "Print Catch"), ("memory", "Closet Match"), ("color", "Color Lab")], max_length=16)),
                ("title", models.CharField(max_length=100)),
                ("title_fa", models.CharField(blank=True, max_length=100)),
                ("description", models.CharField(blank=True, max_length=240)),
                ("description_fa", models.CharField(blank=True, max_length=240)),
                ("is_enabled", models.BooleanField(default=False)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("bronze_score", models.PositiveIntegerField(default=500)),
                ("silver_score", models.PositiveIntegerField(default=1200)),
                ("gold_score", models.PositiveIntegerField(default=2200)),
                ("bronze_points", models.PositiveIntegerField(default=10)),
                ("silver_points", models.PositiveIntegerField(default=25)),
                ("gold_points", models.PositiveIntegerField(default=50)),
                ("score_cap", models.PositiveIntegerField(default=10000)),
                ("max_score_per_second", models.PositiveIntegerField(default=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="GameScore",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("score", models.PositiveIntegerField()),
                ("reward_tier", models.CharField(default="none", max_length=16)),
                ("points_awarded", models.PositiveIntegerField(default=0)),
                ("played_at", models.DateTimeField(auto_now_add=True)),
                ("game", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="scores", to="experience.sologame")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="avan_game_scores", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-score", "played_at"]},
        ),
        migrations.AddIndex(
            model_name="gamescore",
            index=models.Index(fields=["game", "-score"], name="experience_game_score_idx"),
        ),
        migrations.AddIndex(
            model_name="gamescore",
            index=models.Index(fields=["user", "-played_at"], name="experience_user_play_idx"),
        ),
    ]
