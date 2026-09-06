import uuid

from django.conf import settings
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Design(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    class Visibility(models.TextChoices):
        PRIVATE = "private", "Private"
        PUBLIC = "public", "Public"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="designs",
    )
    base_product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="customer_designs",
    )
    base_color = models.ForeignKey(
        "catalog.Color",
        on_delete=models.PROTECT,
        related_name="customer_designs",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=120, default="Untitled Design")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    visibility = models.CharField(max_length=16, choices=Visibility.choices, default=Visibility.PRIVATE)
    allow_remix = models.BooleanField(default=False)
    is_for_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    parent_design = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="remixes",
        null=True,
        blank=True,
    )
    design_data = models.JSONField(default=dict, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status", "visibility", "-published_at"]),
        ]

    def publish(self):
        self.status = self.Status.PUBLISHED
        self.visibility = self.Visibility.PUBLIC
        if not self.published_at:
            self.published_at = timezone.now()
        self.save(update_fields=["status", "visibility", "published_at", "updated_at"])

    def __str__(self):
        return f"{self.title} — {self.owner}"


class DesignAsset(models.Model):
    class Kind(models.TextChoices):
        IMAGE = "image", "Image"
        STICKER = "sticker", "Sticker"
        AI = "ai", "AI generated"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="design_assets",
    )
    image = models.ImageField(upload_to="design-assets/%Y/%m/")
    original_name = models.CharField(max_length=255, blank=True)
    mime_type = models.CharField(max_length=80, blank=True)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.IMAGE)
    source_prompt = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.original_name or str(self.id)


class GarmentMockup(models.Model):
    class Side(models.TextChoices):
        FRONT = "front", "Front"
        BACK = "back", "Back"

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="design_mockups",
    )
    color = models.ForeignKey(
        "catalog.Color",
        on_delete=models.PROTECT,
        related_name="design_mockups",
        null=True,
        blank=True,
    )
    side = models.CharField(max_length=10, choices=Side.choices)
    image = models.ImageField(upload_to="garment-mockups/%Y/%m/")
    print_x = models.DecimalField(max_digits=5, decimal_places=2, default=25)
    print_y = models.DecimalField(max_digits=5, decimal_places=2, default=22)
    print_width = models.DecimalField(max_digits=5, decimal_places=2, default=50)
    print_height = models.DecimalField(max_digits=5, decimal_places=2, default=55)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["product_id", "color_id", "side", "id"]

    def __str__(self):
        color = self.color.name if self.color_id else "Default"
        return f"{self.product} / {color} / {self.side}"


class FabricOption(models.Model):
    name = models.CharField(max_length=80)
    name_fa = models.CharField(max_length=80, blank=True)
    slug = models.SlugField(max_length=90, unique=True)
    roughness = models.FloatField(default=0.72, validators=[MinValueValidator(0), MaxValueValidator(1)])
    weave_strength = models.FloatField(default=0.08, validators=[MinValueValidator(0), MaxValueValidator(1)])
    weave_scale = models.FloatField(default=110, validators=[MinValueValidator(10), MaxValueValidator(400)])
    sheen = models.FloatField(default=0.08, validators=[MinValueValidator(0), MaxValueValidator(1)])
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class GarmentStudioProfile(models.Model):
    class GarmentType(models.TextChoices):
        TEE = "tee", "T-shirt"
        HOODIE = "hoodie", "Hoodie"
        CROP = "crop", "Crop top"

    product = models.OneToOneField(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="studio_profile",
    )
    garment_type = models.CharField(max_length=16, choices=GarmentType.choices, default=GarmentType.TEE)
    default_fabric = models.ForeignKey(
        FabricOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_for_profiles",
    )
    is_enabled = models.BooleanField(default=True)
    front_reference = models.ImageField(upload_to="studio-garments/front/%Y/%m/", blank=True)
    back_reference = models.ImageField(upload_to="studio-garments/back/%Y/%m/", blank=True)
    left_sleeve_reference = models.ImageField(upload_to="studio-garments/left-sleeve/%Y/%m/", blank=True)
    right_sleeve_reference = models.ImageField(upload_to="studio-garments/right-sleeve/%Y/%m/", blank=True)
    model_file = models.FileField(
        upload_to="studio-garments/models/%Y/%m/",
        blank=True,
        validators=[FileExtensionValidator(["glb", "gltf"])],
        help_text="Optional product-specific 3D garment model. GLB is recommended.",
    )
    notes = models.CharField(max_length=220, blank=True)

    @property
    def primary_reference_url(self):
        if self.front_reference:
            return self.front_reference.url
        image = self.product.images.first()
        return image.image.url if image else ""

    @property
    def studio_setup_complete(self):
        # A front visual is enough for the current Studio; a GLB can be added for the real 3D viewer.
        return bool(self.is_enabled and (self.front_reference or self.product.images.exists()))

    def __str__(self):
        return f"{self.product} / {self.get_garment_type_display()}"


class StickerCategory(models.Model):
    name = models.CharField(max_length=80)
    name_fa = models.CharField(max_length=80, blank=True)
    slug = models.SlugField(max_length=90, unique=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "Sticker categories"

    def __str__(self):
        return self.name


class StickerAsset(models.Model):
    category = models.ForeignKey(StickerCategory, on_delete=models.CASCADE, related_name="stickers")
    title = models.CharField(max_length=100)
    title_fa = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to="studio-stickers/%Y/%m/")
    preview_image = models.ImageField(upload_to="studio-stickers/previews/%Y/%m/", blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "title"]

    @property
    def preview_url(self):
        return self.preview_image.url if self.preview_image else self.image.url

    def __str__(self):
        return self.title


class StudioFont(models.Model):
    class LanguageSupport(models.TextChoices):
        BOTH = "both", "Persian + English"
        FA = "fa", "Persian"
        EN = "en", "English"

    name = models.CharField(max_length=80)
    family_name = models.CharField(max_length=120, blank=True, help_text="CSS family/stack for a system font.")
    language_support = models.CharField(max_length=8, choices=LanguageSupport.choices, default=LanguageSupport.BOTH)
    font_file = models.FileField(
        upload_to="studio-fonts/%Y/%m/",
        blank=True,
        validators=[FileExtensionValidator(["woff2", "woff"])],
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    @property
    def css_family(self):
        if self.font_file:
            return f"AVANStudioFont{self.pk}"
        return self.family_name or self.name

    def __str__(self):
        return self.name


class StudioSettings(models.Model):
    singleton_key = models.PositiveSmallIntegerField(default=1, unique=True, editable=False)
    ai_enabled = models.BooleanField(default=True)
    ai_model = models.CharField(max_length=80, default="gpt-image-2")
    allow_user_stickers = models.BooleanField(default=True)
    inspiration_enabled = models.BooleanField(default=True)
    max_upload_mb = models.PositiveSmallIntegerField(default=8, validators=[MinValueValidator(1), MaxValueValidator(25)])
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(singleton_key=1)
        return obj

    def __str__(self):
        return "AVAN Studio settings"


class DesignLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="design_likes",
    )
    design = models.ForeignKey(
        Design,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "design"], name="uniq_design_like")
        ]
        ordering = ["-created_at"]


class DesignSave(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_designs",
    )
    design = models.ForeignKey(
        Design,
        on_delete=models.CASCADE,
        related_name="saves",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "design"], name="uniq_design_save")
        ]
        ordering = ["-created_at"]
