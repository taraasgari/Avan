from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0002_creator_profiles"),
        ("catalog", "0001_initial"),
        ("designs", "0002_marketplace"),
    ]

    operations = [
        migrations.CreateModel(
            name="Challenge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=140)),
                ("slug", models.SlugField(max_length=160, unique=True)),
                ("prompt", models.CharField(max_length=240)),
                ("description", models.TextField(blank=True)),
                ("cover_image", models.ImageField(blank=True, null=True, upload_to="challenges/%Y/%m/")),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published"), ("closed", "Closed")], default="draft", max_length=16)),
                ("starts_at", models.DateTimeField(blank=True, null=True)),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("reward_points", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-starts_at", "-created_at"]},
        ),
        migrations.CreateModel(
            name="Drop",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=140)),
                ("slug", models.SlugField(max_length=160, unique=True)),
                ("subtitle", models.CharField(blank=True, max_length=180)),
                ("description", models.TextField(blank=True)),
                ("cover_image", models.ImageField(blank=True, null=True, upload_to="drops/%Y/%m/")),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published")], default="draft", max_length=16)),
                ("starts_at", models.DateTimeField(blank=True, null=True)),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("is_featured", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-is_featured", "-starts_at", "-created_at"]},
        ),
        migrations.CreateModel(
            name="RewardWallet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("balance", models.IntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="reward_wallet", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="DropItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("label", models.CharField(blank=True, max_length=80)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("design", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="drop_items", to="designs.design")),
                ("drop", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="experience.drop")),
                ("product", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="drop_items", to="catalog.product")),
            ],
            options={"ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="ChallengeEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("note", models.CharField(blank=True, max_length=240)),
                ("status", models.CharField(choices=[("submitted", "Submitted"), ("finalist", "Finalist"), ("winner", "Winner"), ("rejected", "Rejected")], default="submitted", max_length=16)),
                ("reward_granted", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("challenge", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="entries", to="experience.challenge")),
                ("design", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="challenge_entries", to="designs.design")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="challenge_entries", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="RewardTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.IntegerField()),
                ("reason", models.CharField(max_length=180)),
                ("reference", models.CharField(blank=True, max_length=180, null=True, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("wallet", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="transactions", to="experience.rewardwallet")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="challengeentry",
            constraint=models.UniqueConstraint(fields=("challenge", "user", "design"), name="uniq_challenge_user_design"),
        ),
    ]
