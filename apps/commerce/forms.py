from django import forms

from .models import Campaign, CommerceSettings, ShippingRule


class CommerceSettingsForm(forms.ModelForm):
    class Meta:
        model = CommerceSettings
        fields = [
            "payment_provider",
            "free_shipping_threshold",
            "abandoned_cart_hours",
            "pending_payment_timeout_minutes",
            "auto_detect_abandoned_carts",
            "auto_cancel_expired_orders",
        ]


class ShippingRuleForm(forms.ModelForm):
    class Meta:
        model = ShippingRule
        fields = ["method", "name", "province", "city", "minimum_subtotal", "maximum_subtotal", "price_override", "free_over", "priority", "is_active"]


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ["slug", "name", "coupon", "headline_en", "headline_fa", "starts_at", "ends_at", "priority", "is_active"]
        widgets = {
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
