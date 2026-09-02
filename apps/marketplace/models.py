import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class MarketplaceSettings(models.Model):
    creator_pricing_enabled = models.BooleanField(
        default=False,
        help_text="When off, published designs can still be worn/bought but no separate creator design fee is charged.",
    )
    commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="AVAN commission from the creator design fee. Set this before launch.",
    )
    minimum_payout_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
    )
    points_redemption_cost = models.PositiveIntegerField(
        default=0,
        help_text="AVAN Points required for one reward coupon. 0 disables redemption.",
    )
    points_coupon_value = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Fixed Toman value of the coupon created from points.",
    )
    points_coupon_minimum_subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Marketplace settings"
        verbose_name_plural = "Marketplace settings"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        # This is intentionally a singleton configuration row.
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "AVAN Marketplace Settings"


class CreatorWallet(models.Model):
    creator = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="creator_wallet",
    )
    available_balance = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    pending_payout = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    total_earned = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    total_paid = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(available_balance__gte=0), name="creator_wallet_available_gte_0"),
            models.CheckConstraint(condition=models.Q(pending_payout__gte=0), name="creator_wallet_pending_gte_0"),
            models.CheckConstraint(condition=models.Q(total_earned__gte=0), name="creator_wallet_earned_gte_0"),
            models.CheckConstraint(condition=models.Q(total_paid__gte=0), name="creator_wallet_paid_gte_0"),
        ]

    def __str__(self):
        return f"{self.creator} / {self.available_balance} Toman"


class CreatorEarning(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="creator_earnings",
    )
    order_item = models.OneToOneField(
        "orders.OrderItem",
        on_delete=models.PROTECT,
        related_name="creator_earning",
    )
    design = models.ForeignKey(
        "designs.Design",
        on_delete=models.SET_NULL,
        related_name="creator_earnings",
        null=True,
        blank=True,
    )
    design_id_snapshot = models.UUIDField(null=True, blank=True)
    gross_design_fee = models.DecimalField(max_digits=12, decimal_places=0)
    platform_commission = models.DecimalField(max_digits=12, decimal_places=0)
    creator_amount = models.DecimalField(max_digits=12, decimal_places=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.creator} / +{self.creator_amount} / {self.order_item_id}"


class PayoutRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        PAID = "paid", "Paid"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payout_requests",
    )
    amount = models.DecimalField(max_digits=14, decimal_places=0, validators=[MinValueValidator(1)])
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    creator_note = models.CharField(max_length=240, blank=True)
    admin_note = models.CharField(max_length=240, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.creator} / {self.amount} / {self.status}"
