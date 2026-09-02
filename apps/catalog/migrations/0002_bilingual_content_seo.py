from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]

    operations = [
        migrations.AddField(model_name="category", name="name_en", field=models.CharField(blank=True, default="", max_length=120)),
        migrations.AddField(model_name="category", name="name_fa", field=models.CharField(blank=True, default="", max_length=120)),
        migrations.AddField(model_name="category", name="description_en", field=models.TextField(blank=True, default="")),
        migrations.AddField(model_name="category", name="description_fa", field=models.TextField(blank=True, default="")),
        migrations.AddField(model_name="category", name="seo_title_en", field=models.CharField(blank=True, default="", max_length=180)),
        migrations.AddField(model_name="category", name="seo_title_fa", field=models.CharField(blank=True, default="", max_length=180)),
        migrations.AddField(model_name="category", name="seo_description_en", field=models.CharField(blank=True, default="", max_length=320)),
        migrations.AddField(model_name="category", name="seo_description_fa", field=models.CharField(blank=True, default="", max_length=320)),
        migrations.AddField(model_name="product", name="name_en", field=models.CharField(blank=True, default="", max_length=180)),
        migrations.AddField(model_name="product", name="name_fa", field=models.CharField(blank=True, default="", max_length=180)),
        migrations.AddField(model_name="product", name="description_en", field=models.TextField(blank=True, default="")),
        migrations.AddField(model_name="product", name="description_fa", field=models.TextField(blank=True, default="")),
        migrations.AddField(model_name="product", name="seo_title_en", field=models.CharField(blank=True, default="", max_length=180)),
        migrations.AddField(model_name="product", name="seo_title_fa", field=models.CharField(blank=True, default="", max_length=180)),
        migrations.AddField(model_name="product", name="seo_description_en", field=models.CharField(blank=True, default="", max_length=320)),
        migrations.AddField(model_name="product", name="seo_description_fa", field=models.CharField(blank=True, default="", max_length=320)),
    ]
