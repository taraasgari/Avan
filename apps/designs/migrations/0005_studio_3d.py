from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


def seed_studio(apps, schema_editor):
    FabricOption = apps.get_model('designs', 'FabricOption')
    StickerCategory = apps.get_model('designs', 'StickerCategory')
    StudioFont = apps.get_model('designs', 'StudioFont')
    StudioSettings = apps.get_model('designs', 'StudioSettings')

    fabrics = [
        dict(name='Cotton', name_fa='پنبه', slug='cotton', roughness=0.82, weave_strength=0.10, weave_scale=118, sheen=0.04, sort_order=10),
        dict(name='Heavy Cotton', name_fa='پنبه سنگین', slug='heavy-cotton', roughness=0.90, weave_strength=0.16, weave_scale=92, sheen=0.02, sort_order=20),
        dict(name='Jersey', name_fa='جرسی', slug='jersey', roughness=0.68, weave_strength=0.08, weave_scale=145, sheen=0.08, sort_order=30),
        dict(name='Polyester', name_fa='پلی‌استر', slug='polyester', roughness=0.42, weave_strength=0.05, weave_scale=170, sheen=0.30, sort_order=40),
    ]
    for item in fabrics:
        FabricOption.objects.update_or_create(slug=item['slug'], defaults=item)

    for order, (name, name_fa, slug) in enumerate([
        ('Shapes', 'شکل‌ها', 'shapes'),
        ('Street', 'استریت', 'street'),
        ('Persian', 'ایرانی', 'persian'),
        ('Icons', 'آیکن‌ها', 'icons'),
    ], start=1):
        StickerCategory.objects.update_or_create(
            slug=slug,
            defaults={'name': name, 'name_fa': name_fa, 'sort_order': order * 10, 'is_active': True},
        )

    fonts = [
        ('Tahoma', 'Tahoma, Arial, sans-serif', 'both', 10),
        ('Arial', 'Arial, sans-serif', 'both', 20),
        ('Georgia', 'Georgia, serif', 'en', 30),
        ('Times New Roman', '"Times New Roman", serif', 'both', 40),
        ('Courier New', '"Courier New", monospace', 'en', 50),
    ]
    for name, family, language, order in fonts:
        StudioFont.objects.update_or_create(
            name=name,
            defaults={'family_name': family, 'language_support': language, 'sort_order': order, 'is_active': True},
        )

    StudioSettings.objects.get_or_create(singleton_key=1)


class Migration(migrations.Migration):
    dependencies = [
        ('designs', '0004_design_sale_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='designasset',
            name='kind',
            field=models.CharField(choices=[('image', 'Image'), ('sticker', 'Sticker'), ('ai', 'AI generated')], default='image', max_length=16),
        ),
        migrations.AddField(
            model_name='designasset',
            name='source_prompt',
            field=models.TextField(blank=True),
        ),
        migrations.CreateModel(
            name='FabricOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80)),
                ('name_fa', models.CharField(blank=True, max_length=80)),
                ('slug', models.SlugField(max_length=90, unique=True)),
                ('roughness', models.FloatField(default=0.72, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('weave_strength', models.FloatField(default=0.08, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('weave_scale', models.FloatField(default=110, validators=[django.core.validators.MinValueValidator(10), django.core.validators.MaxValueValidator(400)])),
                ('sheen', models.FloatField(default=0.08, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('is_active', models.BooleanField(default=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
            ],
            options={'ordering': ['sort_order', 'name']},
        ),
        migrations.CreateModel(
            name='StickerCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80)),
                ('name_fa', models.CharField(blank=True, max_length=80)),
                ('slug', models.SlugField(max_length=90, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
            ],
            options={'verbose_name_plural': 'Sticker categories', 'ordering': ['sort_order', 'name']},
        ),
        migrations.CreateModel(
            name='StudioFont',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80)),
                ('family_name', models.CharField(blank=True, help_text='CSS family/stack for a system font.', max_length=120)),
                ('language_support', models.CharField(choices=[('both', 'Persian + English'), ('fa', 'Persian'), ('en', 'English')], default='both', max_length=8)),
                ('font_file', models.FileField(blank=True, upload_to='studio-fonts/%Y/%m/', validators=[django.core.validators.FileExtensionValidator(['woff2', 'woff'])])),
                ('is_active', models.BooleanField(default=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
            ],
            options={'ordering': ['sort_order', 'name']},
        ),
        migrations.CreateModel(
            name='StudioSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('singleton_key', models.PositiveSmallIntegerField(default=1, editable=False, unique=True)),
                ('ai_enabled', models.BooleanField(default=True)),
                ('ai_model', models.CharField(default='gpt-image-2', max_length=80)),
                ('allow_user_stickers', models.BooleanField(default=True)),
                ('inspiration_enabled', models.BooleanField(default=True)),
                ('max_upload_mb', models.PositiveSmallIntegerField(default=8, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(25)])),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='GarmentStudioProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('garment_type', models.CharField(choices=[('tee', 'T-shirt'), ('hoodie', 'Hoodie'), ('crop', 'Crop top')], default='tee', max_length=16)),
                ('is_enabled', models.BooleanField(default=True)),
                ('notes', models.CharField(blank=True, max_length=220)),
                ('default_fabric', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='default_for_profiles', to='designs.fabricoption')),
                ('product', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='studio_profile', to='catalog.product')),
            ],
        ),
        migrations.CreateModel(
            name='StickerAsset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('title_fa', models.CharField(blank=True, max_length=100)),
                ('image', models.ImageField(upload_to='studio-stickers/%Y/%m/')),
                ('preview_image', models.ImageField(blank=True, upload_to='studio-stickers/previews/%Y/%m/')),
                ('is_active', models.BooleanField(default=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stickers', to='designs.stickercategory')),
            ],
            options={'ordering': ['sort_order', 'title']},
        ),
        migrations.RunPython(seed_studio, migrations.RunPython.noop),
    ]
