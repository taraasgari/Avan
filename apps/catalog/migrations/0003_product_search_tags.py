from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_bilingual_content_seo"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="search_tags",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Comma-separated search tags/keywords set by the owner.",
                max_length=500,
            ),
        ),
    ]
