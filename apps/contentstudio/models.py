from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


class MediaAsset(models.Model):
    class Kind(models.TextChoices):
        IMAGE = "image", "Image"
        BANNER = "banner", "Banner"
        EDITORIAL = "editorial", "Editorial"

    title = models.CharField(max_length=180, blank=True)
    file = models.ImageField(
        upload_to="content/%Y/%m/",
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp", "gif"])],
    )
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.IMAGE)
    alt_en = models.CharField(max_length=220, blank=True)
    alt_fa = models.CharField(max_length=220, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="content_media_uploads",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.title or self.file.name

    def localized_alt(self, language="en"):
        if str(language).lower().startswith("fa"):
            return self.alt_fa or self.alt_en or self.title
        return self.alt_en or self.alt_fa or self.title


class Collection(models.Model):
    slug = models.SlugField(max_length=160, unique=True)
    name_en = models.CharField(max_length=180)
    name_fa = models.CharField(max_length=180, blank=True)
    description_en = models.TextField(blank=True)
    description_fa = models.TextField(blank=True)
    hero = models.ForeignKey(
        MediaAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hero_collections",
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    products = models.ManyToManyField(
        "catalog.Product",
        through="CollectionItem",
        related_name="content_collections",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name_en", "id"]

    def __str__(self):
        return self.name_en or self.name_fa or self.slug

    def localized_name(self, language="en"):
        if str(language).lower().startswith("fa"):
            return self.name_fa or self.name_en
        return self.name_en or self.name_fa

    def localized_description(self, language="en"):
        if str(language).lower().startswith("fa"):
            return self.description_fa or self.description_en
        return self.description_en or self.description_fa


class CollectionItem(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="collection_items")
    sort_order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["collection", "product"], name="uniq_content_collection_product")
        ]

    def __str__(self):
        return f"{self.collection} / {self.product}"


class SeoPage(models.Model):
    path = models.CharField(max_length=300, unique=True, help_text="Absolute path, for example /about/ or /shop/")
    title_en = models.CharField(max_length=180, blank=True)
    title_fa = models.CharField(max_length=180, blank=True)
    description_en = models.CharField(max_length=320, blank=True)
    description_fa = models.CharField(max_length=320, blank=True)
    canonical_path = models.CharField(max_length=300, blank=True)
    noindex = models.BooleanField(default=False)
    json_ld = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["path"]

    def __str__(self):
        return self.path

    def localized_title(self, language="en"):
        if str(language).lower().startswith("fa"):
            return self.title_fa or self.title_en
        return self.title_en or self.title_fa

    def localized_description(self, language="en"):
        if str(language).lower().startswith("fa"):
            return self.description_fa or self.description_en
        return self.description_en or self.description_fa


class CatalogImportJob(models.Model):
    class Status(models.TextChoices):
        VALIDATED = "validated", "Validated"
        IMPORTED = "imported", "Imported"
        FAILED = "failed", "Failed"

    file_name = models.CharField(max_length=240)
    status = models.CharField(max_length=20, choices=Status.choices)
    total_rows = models.PositiveIntegerField(default=0)
    successful_rows = models.PositiveIntegerField(default=0)
    errors = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="catalog_import_jobs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.file_name} ({self.status})"
