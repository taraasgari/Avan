from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models


HEX_COLOR = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message="Use a 6-digit hex color such as #D50000.",
)


class OwnerSettings(models.Model):
    store_name = models.CharField(max_length=80, default="AVAN")
    support_email = models.EmailField(blank=True)
    support_phone = models.CharField(max_length=30, blank=True)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    operations_note = models.CharField(max_length=240, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Owner settings"
        verbose_name_plural = "Owner settings"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.store_name} owner settings"


class SiteAppearance(models.Model):
    """Safe, structured storefront appearance controls.

    The visual editor intentionally stores a constrained set of design tokens rather
    than arbitrary CSS. That keeps previews fast and avoids turning the Owner Console
    into an XSS/CSS-injection surface.
    """

    primary_color = models.CharField(max_length=7, default="#D50000", validators=[HEX_COLOR])
    light_background = models.CharField(max_length=7, default="#FFFFFF", validators=[HEX_COLOR])
    light_surface = models.CharField(max_length=7, default="#F7F7F7", validators=[HEX_COLOR])
    dark_background = models.CharField(max_length=7, default="#0D0D0F", validators=[HEX_COLOR])
    dark_surface = models.CharField(max_length=7, default="#17171A", validators=[HEX_COLOR])

    base_font_size = models.PositiveSmallIntegerField(
        default=17,
        validators=[MinValueValidator(15), MaxValueValidator(22)],
        help_text="Base English/interface font size in pixels.",
    )
    persian_font_size = models.PositiveSmallIntegerField(
        default=18,
        validators=[MinValueValidator(16), MaxValueValidator(24)],
        help_text="Base Persian interface font size in pixels.",
    )
    content_width = models.PositiveSmallIntegerField(
        default=1440,
        validators=[MinValueValidator(1080), MaxValueValidator(1800)],
        help_text="Maximum content width in pixels.",
    )
    page_gutter = models.PositiveSmallIntegerField(
        default=32,
        validators=[MinValueValidator(16), MaxValueValidator(72)],
        help_text="Desktop page side padding in pixels.",
    )
    header_height = models.PositiveSmallIntegerField(
        default=76,
        validators=[MinValueValidator(64), MaxValueValidator(96)],
        help_text="Desktop header height in pixels.",
    )
    section_spacing = models.PositiveSmallIntegerField(
        default=72,
        validators=[MinValueValidator(40), MaxValueValidator(120)],
        help_text="Vertical spacing between major page sections.",
    )
    card_radius = models.PositiveSmallIntegerField(
        default=12,
        validators=[MinValueValidator(0), MaxValueValidator(28)],
        help_text="Card corner radius in pixels.",
    )
    button_radius = models.PositiveSmallIntegerField(
        default=8,
        validators=[MinValueValidator(0), MaxValueValidator(28)],
        help_text="Button/input corner radius in pixels.",
    )
    card_shadow = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site appearance"
        verbose_name_plural = "Site appearance"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return "AVAN site appearance"


class PageDesign(models.Model):
    """Draft/published visual settings for a storefront page.

    Only structured tokens and copy are stored here; arbitrary HTML/JS is intentionally
    not supported. This keeps the visual editor safe enough for delegated staff use.
    """

    page_key = models.SlugField(max_length=80, unique=True)
    page_label_fa = models.CharField(max_length=120)
    page_label_en = models.CharField(max_length=120)
    page_path = models.CharField(max_length=240)
    draft_data = models.JSONField(default=dict, blank=True)
    published_data = models.JSONField(default=dict, blank=True)
    updated_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_page_designs"
    )
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["page_key"]

    def __str__(self):
        return self.page_label_fa or self.page_label_en or self.page_key
