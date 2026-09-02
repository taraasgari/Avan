from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalog", "0002_bilingual_content_seo"),
    ]

    operations = [
        migrations.CreateModel(
            name="CatalogImportJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file_name", models.CharField(max_length=240)),
                ("status", models.CharField(choices=[("validated", "Validated"), ("imported", "Imported"), ("failed", "Failed")], max_length=20)),
                ("total_rows", models.PositiveIntegerField(default=0)),
                ("successful_rows", models.PositiveIntegerField(default=0)),
                ("errors", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="catalog_import_jobs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="MediaAsset",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(blank=True, max_length=180)),
                ("file", models.ImageField(upload_to="content/%Y/%m/", validators=[django.core.validators.FileExtensionValidator(["jpg", "jpeg", "png", "webp", "gif"])])),
                ("kind", models.CharField(choices=[("image", "Image"), ("banner", "Banner"), ("editorial", "Editorial")], default="image", max_length=20)),
                ("alt_en", models.CharField(blank=True, max_length=220)),
                ("alt_fa", models.CharField(blank=True, max_length=220)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="content_media_uploads", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="SeoPage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("path", models.CharField(help_text="Absolute path, for example /about/ or /shop/", max_length=300, unique=True)),
                ("title_en", models.CharField(blank=True, max_length=180)),
                ("title_fa", models.CharField(blank=True, max_length=180)),
                ("description_en", models.CharField(blank=True, max_length=320)),
                ("description_fa", models.CharField(blank=True, max_length=320)),
                ("canonical_path", models.CharField(blank=True, max_length=300)),
                ("noindex", models.BooleanField(default=False)),
                ("json_ld", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["path"]},
        ),
        migrations.CreateModel(
            name="Collection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(max_length=160, unique=True)),
                ("name_en", models.CharField(max_length=180)),
                ("name_fa", models.CharField(blank=True, max_length=180)),
                ("description_en", models.TextField(blank=True)),
                ("description_fa", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("is_featured", models.BooleanField(default=False)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("starts_at", models.DateTimeField(blank=True, null=True)),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("hero", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="hero_collections", to="contentstudio.mediaasset")),
            ],
            options={"ordering": ["sort_order", "name_en", "id"]},
        ),
        migrations.CreateModel(
            name="CollectionItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_featured", models.BooleanField(default=False)),
                ("collection", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="contentstudio.collection")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="collection_items", to="catalog.product")),
            ],
            options={"ordering": ["sort_order", "id"]},
        ),
        migrations.AddField(
            model_name="collection",
            name="products",
            field=models.ManyToManyField(blank=True, related_name="content_collections", through="contentstudio.CollectionItem", to="catalog.product"),
        ),
        migrations.AddConstraint(
            model_name="collectionitem",
            constraint=models.UniqueConstraint(fields=("collection", "product"), name="uniq_content_collection_product"),
        ),
    ]
