from django.conf import settings
from django.db import models


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "product"], name="uniq_wishlist_user_product")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} / {self.product}"
