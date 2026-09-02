import uuid

from django.conf import settings
from django.db import models


class CommerceSettings(models.Model):
    """Singleton launch controls for commerce behavior.

    Values default to conservative/off states so Stage 10 does not silently change
    existing business decisions before the owner explicitly enables them.
    """

    payment_provider = models.CharField(max_length=50, default="dev")
    free_shipping_threshold = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    abandoned_cart_hours = models.PositiveSmallIntegerField(default=24)
    pending_payment_timeout_minutes = models.PositiveSmallIntegerField(default=30)
    auto_detect_abandoned_carts = models.BooleanField(default=True)
    auto_cancel_expired_orders = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "AVAN Commerce Settings"


class ShippingRule(models.Model):
    method = models.ForeignKey("operations.ShippingMethod", on_delete=models.CASCADE, related_name="commerce_rules")
    name = models.CharField(max_length=120)
    province = models.CharField(max_length=80, blank=True, help_text="Blank means every province.")
    city = models.CharField(max_length=80, blank=True, help_text="Blank means every city.")
    minimum_subtotal = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    maximum_subtotal = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    price_override = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    free_over = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    priority = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["priority", "id"]

    def __str__(self):
        return f"{self.method.code} / {self.name}"


class Campaign(models.Model):
    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=140)
    coupon = models.ForeignKey("coupons.Coupon", on_delete=models.SET_NULL, null=True, blank=True, related_name="campaigns")
    headline_en = models.CharField(max_length=180, blank=True)
    headline_fa = models.CharField(max_length=180, blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    priority = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["priority", "-created_at"]

    def __str__(self):
        return self.name


class AbandonedCartEvent(models.Model):
    class Status(models.TextChoices):
        DETECTED = "detected", "Detected"
        RECOVERED = "recovered", "Recovered"
        DISMISSED = "dismissed", "Dismissed"

    cart = models.OneToOneField("cart.Cart", on_delete=models.CASCADE, related_name="abandoned_event")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DETECTED)
    item_count = models.PositiveIntegerField(default=0)
    value_snapshot = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    detected_at = models.DateTimeField(auto_now_add=True)
    recovered_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-detected_at"]

    def __str__(self):
        return f"{self.cart.token} / {self.status}"


class Refund(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        PROCESSING = "processing", "Processing"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    order = models.ForeignKey("orders.Order", on_delete=models.PROTECT, related_name="refunds")
    return_request = models.ForeignKey("operations.ReturnRequest", on_delete=models.SET_NULL, null=True, blank=True, related_name="refunds")
    payment_attempt = models.ForeignKey("payments.PaymentAttempt", on_delete=models.SET_NULL, null=True, blank=True, related_name="refunds")
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.REQUESTED)
    provider = models.CharField(max_length=50, blank=True)
    external_reference = models.CharField(max_length=180, blank=True)
    reason = models.CharField(max_length=240, blank=True)
    owner_note = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="requested_refunds")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_refunds")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Refund {self.id} / {self.order.number} / {self.status}"


class FulfillmentEvent(models.Model):
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="fulfillment_events")
    event = models.CharField(max_length=80)
    from_status = models.CharField(max_length=40, blank=True)
    to_status = models.CharField(max_length=40, blank=True)
    note = models.CharField(max_length=240, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="fulfillment_events")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.number} / {self.event}"
