from rest_framework import serializers

from apps.catalog.models import ProductVariant
from .models import Cart, CartItem
from .services import available_stock, cart_totals


class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    product_slug = serializers.CharField(source="variant.product.slug", read_only=True)
    product_image = serializers.SerializerMethodField()
    sku = serializers.CharField(source="variant.sku", read_only=True)
    color = serializers.CharField(source="variant.color.name", read_only=True)
    size = serializers.CharField(source="variant.size.name", read_only=True)
    unit_price = serializers.SerializerMethodField()
    garment_unit_price = serializers.DecimalField(source="variant.price", max_digits=12, decimal_places=0, read_only=True)
    design_fee = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    line_total = serializers.SerializerMethodField()
    available_stock = serializers.SerializerMethodField()
    is_customized = serializers.BooleanField(read_only=True)
    design_id = serializers.UUIDField(source="design.id", read_only=True, allow_null=True)
    design_title = serializers.CharField(source="design.title", read_only=True, allow_null=True)
    design_owner = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id", "variant", "product", "product_slug", "product_image", "sku", "color", "size",
            "quantity", "unit_price", "garment_unit_price", "design_fee", "line_total", "available_stock", "is_customized",
            "design_id", "design_title", "design_owner",
        ]
        extra_kwargs = {"variant": {"queryset": ProductVariant.objects.filter(is_active=True)}}

    def get_product(self, obj):
        if obj.design_id:
            return f"{obj.variant.product.name} / {obj.design.title}"
        return obj.variant.product.name

    def get_product_image(self, obj):
        if obj.design_id:
            mockup = (
                obj.variant.product.design_mockups
                .filter(side="front", color=obj.variant.color)
                .first()
                or obj.variant.product.design_mockups.filter(side="front", color__isnull=True).first()
            )
            if mockup:
                try:
                    return mockup.image.url
                except ValueError:
                    pass
        image = obj.variant.product.images.first()
        if not image:
            return None
        try:
            return image.image.url
        except ValueError:
            return None

    def get_unit_price(self, obj):
        return obj.unit_price_total

    def get_line_total(self, obj):
        return obj.unit_price_total * obj.quantity

    def get_available_stock(self, obj):
        return available_stock(obj.variant)

    def get_design_owner(self, obj):
        if not obj.design_id:
            return None
        return obj.design.owner.display_name or obj.design.owner.username


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    totals = serializers.SerializerMethodField()
    coupon_code = serializers.CharField(source="coupon.code", read_only=True, allow_null=True)

    class Meta:
        model = Cart
        fields = ["token", "status", "coupon_code", "items", "totals", "created_at", "updated_at"]

    def get_totals(self, obj):
        return cart_totals(obj)
