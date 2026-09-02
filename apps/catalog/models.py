from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


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
        constraints = [
            models.UniqueConstraint(fields=["product", "color", "size"], name="uniq_product_color_size")
        ]

    @property
    def price(self):
        return self.price_override if self.price_override is not None else self.product.base_price

    @property
    def available_stock(self):
        # Lazy import keeps catalog independent from the order app at import time.
        from django.utils import timezone
        from apps.orders.models import StockReservation

        reserved = sum(
            StockReservation.objects.filter(
                variant_id=self.id,
                status=StockReservation.Status.ACTIVE,
                expires_at__gt=timezone.now(),
            ).values_list("quantity", flat=True)
        )
        return max(0, int(self.stock) - reserved)

    def __str__(self):
        return f"{self.product} / {self.color} / {self.size}"
