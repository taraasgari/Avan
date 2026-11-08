from django.db import migrations, models
import django.db.models.deletion

PAGES = [
    ("home", "صفحه اصلی", "Home", "/"),
    ("shop", "فروشگاه", "Shop", "/shop/"),
    ("product", "صفحه محصول", "Product detail", "/shop/"),
    ("design", "انتخاب لباس برای طراحی", "Design garments", "/design/garments/"),
    ("studio", "استودیو طراحی", "Design studio", "/design/"),
    ("collections", "کالکشن‌ها", "Collections", "/collections/"),
    ("explore", "کاوش", "Explore", "/explore/"),
    ("play", "بازی‌ها", "Play", "/play/"),
    ("challenges", "چالش‌ها", "Challenges", "/challenges/"),
    ("drops", "دراپ‌ها", "Drops", "/drops/"),
    ("account", "حساب کاربری", "Account", "/account/"),
    ("support", "پشتیبانی", "Support", "/account/support/"),
]


def seed_pages(apps, schema_editor):
    PageDesign = apps.get_model("owner", "PageDesign")
    for key, fa, en, path in PAGES:
        PageDesign.objects.get_or_create(page_key=key, defaults={"page_label_fa": fa, "page_label_en": en, "page_path": path})


class Migration(migrations.Migration):
    dependencies = [("owner", "0002_siteappearance"), ("accounts", "0005_support_ticket_order")]
    operations = [
        migrations.CreateModel(
            name="PageDesign",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("page_key", models.SlugField(max_length=80, unique=True)),
                ("page_label_fa", models.CharField(max_length=120)),
                ("page_label_en", models.CharField(max_length=120)),
                ("page_path", models.CharField(max_length=240)),
                ("draft_data", models.JSONField(blank=True, default=dict)),
                ("published_data", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="updated_page_designs", to="accounts.user")),
            ],
            options={"ordering": ["page_key"]},
        ),
        migrations.RunPython(seed_pages, migrations.RunPython.noop),
    ]
