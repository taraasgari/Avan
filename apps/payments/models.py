import uuid
from django.db import models


class PaymentAttempt(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        REDIRECTED = "redirected", "Redirected"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        REQUIRES_REVIEW = "requires_review", "Requires review"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="payment_attempts")
    provider = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    external_reference = models.CharField(max_length=160, blank=True)
    redirect_url = models.URLField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.provider} / {self.order_id} / {self.status}"
