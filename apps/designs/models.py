import uuid

from django.conf import settings
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="design_assets",
    )
    image = models.ImageField(upload_to="design-assets/%Y/%m/")
    original_name = models.CharField(max_length=255, blank=True)
    mime_type = models.CharField(max_length=80, blank=True)
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
