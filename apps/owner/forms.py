from django import forms

from apps.catalog.models import Product
from apps.marketplace.models import MarketplaceSettings

from .models import OwnerSettings


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "slug",
            "category",
            "description",
            "base_price",
            "product_type",
            "is_active",
            "is_featured",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
        }


class OwnerSettingsForm(forms.ModelForm):
    class Meta:
        model = OwnerSettings
        fields = [
            "store_name",
            "support_email",
            "support_phone",
            "low_stock_threshold",
            "operations_note",
        ]


class MarketplaceSettingsForm(forms.ModelForm):
    class Meta:
        model = MarketplaceSettings
        fields = [
            "creator_pricing_enabled",
            "commission_percent",
            "minimum_payout_amount",
            "points_redemption_cost",
            "points_coupon_value",
            "points_coupon_minimum_subtotal",
        ]
