from rest_framework import serializers
from .models import Product, ProductVariant


def _request_language(serializer):
    request = serializer.context.get("request") if serializer.context else None
    value = getattr(request, "avan_language", None) or getattr(request, "LANGUAGE_CODE", None) or "en"
    return "fa" if str(value).lower().startswith("fa") else "en"


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
    category = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "category", "description", "base_price", "product_type", "variants"]

    def get_name(self, obj):
        return obj.localized_name(_request_language(self))

    def get_description(self, obj):
        return obj.localized_description(_request_language(self))

    def get_category(self, obj):
        return obj.category.localized_name(_request_language(self))
