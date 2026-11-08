import secrets
import string
import uuid

from django.conf import settings
from django.db import models


TRACKING_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _token(length=6):
    return "".join(secrets.choice(TRACKING_ALPHABET) for _ in range(length))


def generate_order_tracking_code():
    from django.utils import timezone
    return f"AVN-{timezone.localdate():%y%m%d}-{_token(5)}"


def generate_item_tracking_code():
    return f"AVN-I-{_token(8)}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        PAID = "paid", "Paid"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        NEEDS_REVIEW = "needs_review", "Needs review"

    number = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    tracking_code = models.CharField(max_length=32, unique=True, blank=True, db_index=True)
    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="orders", null=True, blank=True)
    cart = models.ForeignKey("cart.Cart", on_delete=models.SET_NULL, related_name="orders", null=True, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING_PAYMENT)
    subtotal = models.DecimalField(max_digits=12, decimal_places=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=0)
    customer_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    province = models.CharField(max_length=80)
    city = models.CharField(max_length=80)
    address = models.TextField()
    postal_code = models.CharField(max_length=30, blank=True)
    customer_note = models.TextField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            for _ in range(12):
                candidate = generate_order_tracking_code()
                if not type(self).objects.filter(tracking_code=candidate).exists():
                    self.tracking_code = candidate
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return self.tracking_code or str(self.number)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    item_tracking_code = models.CharField(max_length=32, unique=True, blank=True, db_index=True)
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.PROTECT, related_name="order_items")
    product_name = models.CharField(max_length=180)
    sku = models.CharField(max_length=80)
    color_name = models.CharField(max_length=60)
    size_name = models.CharField(max_length=30)
    unit_price = models.DecimalField(max_digits=12, decimal_places=0)
    garment_unit_price = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    design_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    creator_id_snapshot = models.PositiveBigIntegerField(null=True, blank=True)
    platform_commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    platform_commission_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    creator_earning_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=12, decimal_places=0)
    is_customized = models.BooleanField(default=False)
    design_id_snapshot = models.UUIDField(null=True, blank=True)
    design_title = models.CharField(max_length=120, blank=True)
    design_owner_name = models.CharField(max_length=120, blank=True)
    design_snapshot = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        if not self.item_tracking_code:
            for _ in range(12):
                candidate = generate_item_tracking_code()
                if not type(self).objects.filter(item_tracking_code=candidate).exists():
                    self.item_tracking_code = candidate
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"


class StockReservation(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        CONSUMED = "consumed", "Consumed"
        RELEASED = "released", "Released"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="reservations")
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.CASCADE, related_name="reservations")
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["variant", "status", "expires_at"])]

    def __str__(self):
        return f"{self.order_id} / {self.variant_id} / {self.quantity}"
