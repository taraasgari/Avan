from rest_framework import serializers
from .models import Product, ProductVariant


class ProductVariantSerializer(serializers.ModelSerializer):
    color = serializers.CharField(source="color.name")
    size = serializers.CharField(source="size.name")
    price = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    available_stock = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = ["id", "sku", "color", "size", "stock", "available_stock", "price"]


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    category = serializers.CharField(source="category.name")

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "category", "description", "base_price", "product_type", "variants"]
