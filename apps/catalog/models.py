from django.db import models


def _is_fa(language):
    return str(language or "").lower().startswith("fa")


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    name_en = models.CharField(max_length=120, blank=True, default="")
    name_fa = models.CharField(max_length=120, blank=True, default="")
    description_en = models.TextField(blank=True, default="")
    description_fa = models.TextField(blank=True, default="")
    seo_title_en = models.CharField(max_length=180, blank=True, default="")
    seo_title_fa = models.CharField(max_length=180, blank=True, default="")
    seo_description_en = models.CharField(max_length=320, blank=True, default="")
    seo_description_fa = models.CharField(max_length=320, blank=True, default="")
    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def localized_name(self, language="en"):
        return (self.name_fa or self.name_en or self.name) if _is_fa(language) else (self.name_en or self.name_fa or self.name)

    def localized_description(self, language="en"):
        return (self.description_fa or self.description_en) if _is_fa(language) else (self.description_en or self.description_fa)


class Color(models.Model):
    name = models.CharField(max_length=60)
    slug = models.SlugField(max_length=80, unique=True)
    hex_code = models.CharField(max_length=7, blank=True)

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=30)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    class ProductType(models.TextChoices):
        READY = "ready", "Ready design"
        CUSTOMIZABLE = "customizable", "Customizable"

    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=12, decimal_places=0)
    product_type = models.CharField(max_length=20, choices=ProductType.choices, default=ProductType.READY)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    name_en = models.CharField(max_length=180, blank=True, default="")
    name_fa = models.CharField(max_length=180, blank=True, default="")
    description_en = models.TextField(blank=True, default="")
    description_fa = models.TextField(blank=True, default="")
    seo_title_en = models.CharField(max_length=180, blank=True, default="")
    seo_title_fa = models.CharField(max_length=180, blank=True, default="")
    seo_description_en = models.CharField(max_length=320, blank=True, default="")
    seo_description_fa = models.CharField(max_length=320, blank=True, default="")
    search_tags = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Comma-separated search tags/keywords set by the owner.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def localized_name(self, language="en"):
        return (self.name_fa or self.name_en or self.name) if _is_fa(language) else (self.name_en or self.name_fa or self.name)

    def localized_description(self, language="en"):
        return (self.description_fa or self.description_en or self.description) if _is_fa(language) else (self.description_en or self.description_fa or self.description)

    def localized_seo_title(self, language="en"):
        if _is_fa(language):
            return self.seo_title_fa or self.name_fa or self.seo_title_en or self.name_en or self.name
        return self.seo_title_en or self.name_en or self.seo_title_fa or self.name_fa or self.name

    def localized_seo_description(self, language="en"):
        if _is_fa(language):
            return self.seo_description_fa or self.description_fa or self.seo_description_en or self.description_en or self.description
        return self.seo_description_en or self.description_en or self.seo_description_fa or self.description_fa or self.description


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/%Y/%m/")
    alt_text = models.CharField(max_length=180, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    color = models.ForeignKey(Color, on_delete=models.PROTECT, related_name="variants")
    size = models.ForeignKey(Size, on_delete=models.PROTECT, related_name="variants")
    sku = models.CharField(max_length=80, unique=True)
    stock = models.PositiveIntegerField(default=0)
    price_override = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["product", "color", "size"], name="uniq_product_color_size")]

    @property
    def price(self):
        return self.price_override if self.price_override is not None else self.product.base_price

    @property
    def available_stock(self):
        from django.utils import timezone
        from apps.orders.models import StockReservation
        reserved = sum(StockReservation.objects.filter(variant_id=self.id, status=StockReservation.Status.ACTIVE, expires_at__gt=timezone.now()).values_list("quantity", flat=True))
        return max(0, int(self.stock) - reserved)

    def __str__(self):
        return f"{self.product} / {self.color} / {self.size}"
