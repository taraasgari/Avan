from django.conf import settings
from django.db import models


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_addresses")
    title = models.CharField(max_length=60, default="Home")
    recipient_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    province = models.CharField(max_length=80)
    city = models.CharField(max_length=80)
    address = models.TextField()
    postal_code = models.CharField(max_length=30, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "-updated_at"]

    def __str__(self):
        return f"{self.user} / {self.title}"


class ShippingMethod(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name_en = models.CharField(max_length=100)
    name_fa = models.CharField(max_length=100)
    base_price = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    estimated_days_min = models.PositiveSmallIntegerField(default=1)
    estimated_days_max = models.PositiveSmallIntegerField(default=3)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name_en


class Shipment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PACKING = "packing", "Packing"
        READY = "ready", "Ready to ship"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        RETURNED = "returned", "Returned"

    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE, related_name="shipment")
    method = models.ForeignKey(ShippingMethod, on_delete=models.PROTECT, related_name="shipments", null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    carrier_name = models.CharField(max_length=100, blank=True)
    tracking_code = models.CharField(max_length=120, blank=True, db_index=True)
    owner_note = models.TextField(blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order.number} / {self.status}"


class ReturnRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        RECEIVED = "received", "Item received"
        REFUND_PENDING = "refund_pending", "Refund pending"
        REFUNDED = "refunded", "Refunded"
        CLOSED = "closed", "Closed"

    class Reason(models.TextChoices):
        SIZE = "size", "Size / fit issue"
        DAMAGED = "damaged", "Damaged item"
        WRONG_ITEM = "wrong_item", "Wrong item"
        QUALITY = "quality", "Quality issue"
        OTHER = "other", "Other"

    order = models.ForeignKey("orders.Order", on_delete=models.PROTECT, related_name="return_requests")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="return_requests")
    reason = models.CharField(max_length=24, choices=Reason.choices)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.REQUESTED)
    customer_note = models.TextField(blank=True)
    owner_note = models.TextField(blank=True)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Return {self.pk} / {self.order.number}"


class InventoryMovement(models.Model):
    class Kind(models.TextChoices):
        RESTOCK = "restock", "Restock"
        ADJUSTMENT = "adjustment", "Manual adjustment"
        RETURN = "return", "Customer return"
        PRODUCTION = "production", "Production received"
        DAMAGE = "damage", "Damage / write-off"

    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.PROTECT, related_name="inventory_movements")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    delta = models.IntegerField()
    stock_before = models.PositiveIntegerField()
    stock_after = models.PositiveIntegerField()
    note = models.CharField(max_length=240, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="inventory_movements")
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="inventory_movements")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.variant.sku} {self.delta:+d}"


class Supplier(models.Model):
    name = models.CharField(max_length=140)
    contact_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductionBatch(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        IN_PROGRESS = "in_progress", "In progress"
        READY = "ready", "Ready"
        RECEIVED = "received", "Received into stock"
        CANCELLED = "cancelled", "Cancelled"

    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="production_batches")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name="production_batches")
    reference = models.CharField(max_length=80, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    planned_quantity = models.PositiveIntegerField(default=0)
    completed_quantity = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    expected_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference
