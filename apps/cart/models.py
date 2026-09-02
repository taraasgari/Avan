import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models


class Cart(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CONVERTED = "converted", "Converted"
        ABANDONED = "abandoned", "Abandoned"

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carts",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    coupon = models.ForeignKey(
        "coupons.Coupon",
        on_delete=models.SET_NULL,
        related_name="carts",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Cart {self.token}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.PROTECT, related_name="cart_items")
    design = models.ForeignKey(
        "designs.Design",
        on_delete=models.SET_NULL,
        related_name="cart_items",
        null=True,
        blank=True,
    )
    design_snapshot = models.JSONField(default=dict, blank=True)
    design_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "variant", "design"],
                name="uniq_cart_variant_design",
                nulls_distinct=False,
            )
        ]
        ordering = ["id"]

    @property
    def unit_price_total(self):
        return Decimal(self.variant.price) + Decimal(self.design_fee or 0)

    @property
    def is_customized(self):
        return bool(self.design_id or self.design_snapshot)

    def __str__(self):
        suffix = f" / {self.design.title}" if self.design_id else ""
        return f"{self.variant}{suffix} × {self.quantity}"
