from rest_framework import serializers
from .models import WishlistItem


class WishlistItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)

    class Meta:
        model = WishlistItem
        fields = ["id", "product", "product_name", "product_slug", "created_at"]
