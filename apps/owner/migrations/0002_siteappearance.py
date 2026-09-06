from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("owner", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteAppearance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("primary_color", models.CharField(default="#D50000", max_length=7, validators=[RegexValidator(message="Use a 6-digit hex color such as #D50000.", regex="^#[0-9A-Fa-f]{6}$")])),
                ("light_background", models.CharField(default="#FFFFFF", max_length=7, validators=[RegexValidator(message="Use a 6-digit hex color such as #D50000.", regex="^#[0-9A-Fa-f]{6}$")])),
                ("light_surface", models.CharField(default="#F7F7F7", max_length=7, validators=[RegexValidator(message="Use a 6-digit hex color such as #D50000.", regex="^#[0-9A-Fa-f]{6}$")])),
                ("dark_background", models.CharField(default="#0D0D0F", max_length=7, validators=[RegexValidator(message="Use a 6-digit hex color such as #D50000.", regex="^#[0-9A-Fa-f]{6}$")])),
                ("dark_surface", models.CharField(default="#17171A", max_length=7, validators=[RegexValidator(message="Use a 6-digit hex color such as #D50000.", regex="^#[0-9A-Fa-f]{6}$")])),
                ("base_font_size", models.PositiveSmallIntegerField(default=17, help_text="Base English/interface font size in pixels.", validators=[MinValueValidator(15), MaxValueValidator(22)])),
                ("persian_font_size", models.PositiveSmallIntegerField(default=18, help_text="Base Persian interface font size in pixels.", validators=[MinValueValidator(16), MaxValueValidator(24)])),
                ("content_width", models.PositiveSmallIntegerField(default=1440, help_text="Maximum content width in pixels.", validators=[MinValueValidator(1080), MaxValueValidator(1800)])),
                ("page_gutter", models.PositiveSmallIntegerField(default=32, help_text="Desktop page side padding in pixels.", validators=[MinValueValidator(16), MaxValueValidator(72)])),
                ("header_height", models.PositiveSmallIntegerField(default=76, help_text="Desktop header height in pixels.", validators=[MinValueValidator(64), MaxValueValidator(96)])),
                ("section_spacing", models.PositiveSmallIntegerField(default=72, help_text="Vertical spacing between major page sections.", validators=[MinValueValidator(40), MaxValueValidator(120)])),
                ("card_radius", models.PositiveSmallIntegerField(default=12, help_text="Card corner radius in pixels.", validators=[MinValueValidator(0), MaxValueValidator(28)])),
                ("button_radius", models.PositiveSmallIntegerField(default=8, help_text="Button/input corner radius in pixels.", validators=[MinValueValidator(0), MaxValueValidator(28)])),
                ("card_shadow", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Site appearance",
                "verbose_name_plural": "Site appearance",
            },
        ),
    ]
