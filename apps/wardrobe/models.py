import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class SizePassport(models.Model):
    class Fit(models.TextChoices):
        SLIM = "slim", "Slim"
        REGULAR = "regular", "Regular"
        RELAXED = "relaxed", "Relaxed"
        OVERSIZED = "oversized", "Oversized"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="size_passport",
    )
    height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    weight_kg = models.PositiveSmallIntegerField(null=True, blank=True)
    chest_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    waist_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    hip_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    preferred_fit = models.CharField(
        max_length=16,
        choices=Fit.choices,
        default=Fit.REGULAR,
    )
    usual_top_size = models.ForeignKey(
        "catalog.Size",
        on_delete=models.SET_NULL,
        related_name="size_passports",
        null=True,
        blank=True,
    )
    notes = models.CharField(max_length=240, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} / {self.usual_top_size or 'No size'}"


class Outfit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="outfits",
    )
    title = models.CharField(max_length=120, default="New Outfit")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.title} — {self.owner}"


class OutfitItem(models.Model):
    class Position(models.TextChoices):
        TOP = "top", "Top"
        BOTTOM = "bottom", "Bottom"
        OUTERWEAR = "outerwear", "Outerwear"
        SHOES = "shoes", "Shoes"
        ACCESSORY = "accessory", "Accessory"
        OTHER = "other", "Other"

    outfit = models.ForeignKey(
        Outfit,
        on_delete=models.CASCADE,
        related_name="items",
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.PROTECT,
        related_name="outfit_items",
    )
    position = models.CharField(
        max_length=16,
        choices=Position.choices,
        default=Position.OTHER,
    )
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["outfit", "variant"],
                name="uniq_outfit_variant",
            )
        ]

    def clean(self):
        if self.variant_id and not self.variant.is_active:
            raise ValidationError("Inactive variants cannot be added to an outfit.")

    def __str__(self):
        return f"{self.outfit} / {self.variant}"
