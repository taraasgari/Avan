from rest_framework import serializers

from apps.catalog.models import Product
from .models import Design, DesignAsset
from .validators import validate_design_data


class DesignSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    product_name = serializers.CharField(source="base_product.name", read_only=True)
    product_slug = serializers.CharField(source="base_product.slug", read_only=True)
    color_name = serializers.CharField(source="base_color.name", read_only=True, allow_null=True)
    remix_count = serializers.IntegerField(source="remixes.count", read_only=True)
    like_count = serializers.IntegerField(source="likes.count", read_only=True)
    save_count = serializers.IntegerField(source="saves.count", read_only=True)
    liked_by_me = serializers.SerializerMethodField()
    saved_by_me = serializers.SerializerMethodField()

    class Meta:
        model = Design
        fields = [
            "id", "owner_name", "owner_username", "title", "base_product", "product_name", "product_slug",
            "base_color", "color_name", "status", "visibility", "allow_remix", "is_for_sale",
            "parent_design", "design_data", "remix_count", "like_count", "save_count",
            "liked_by_me", "saved_by_me", "published_at", "created_at", "updated_at",
        ]
        read_only_fields = ["status", "published_at", "parent_design"]

    def get_owner_name(self, obj):
        return obj.owner.display_name or obj.owner.username

    def get_liked_by_me(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.likes.filter(user=request.user).exists())

    def get_saved_by_me(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.saves.filter(user=request.user).exists())

    def validate_base_product(self, value):
        if not value.is_active or value.product_type != Product.ProductType.CUSTOMIZABLE:
            raise serializers.ValidationError("This product cannot be customized.")
        return value

    def validate_design_data(self, value):
        return validate_design_data(value)

    def validate(self, attrs):
        product = attrs.get("base_product") or getattr(self.instance, "base_product", None)
        color = attrs.get("base_color") if "base_color" in attrs else getattr(self.instance, "base_color", None)
        if product and color and not product.variants.filter(color=color, is_active=True).exists():
            raise serializers.ValidationError({"base_color": "This color is not available for the selected garment."})
        return attrs


class DesignAssetSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = DesignAsset
        fields = ["id", "original_name", "mime_type", "url", "created_at"]

    def get_url(self, obj):
        # Keep stored design documents host-independent. The browser can resolve this local media URL.
        return obj.image.url
