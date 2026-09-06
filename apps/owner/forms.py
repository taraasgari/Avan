from django import forms

from apps.catalog.models import Product
from apps.designs.models import FabricOption, GarmentStudioProfile
from apps.growth.security import validate_uploaded_image
from apps.marketplace.models import MarketplaceSettings

from .models import OwnerSettings, SiteAppearance


class ColorInput(forms.TextInput):
    input_type = "color"


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "slug",
            "category",
            "description",
            "search_tags",
            "base_price",
            "product_type",
            "is_active",
            "is_featured",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "search_tags": forms.TextInput(),
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


class SiteAppearanceForm(forms.ModelForm):
    class Meta:
        model = SiteAppearance
        fields = [
            "primary_color",
            "light_background",
            "light_surface",
            "dark_background",
            "dark_surface",
            "base_font_size",
            "persian_font_size",
            "content_width",
            "page_gutter",
            "header_height",
            "section_spacing",
            "card_radius",
            "button_radius",
            "card_shadow",
        ]
        widgets = {
            "primary_color": ColorInput(attrs={"data-appearance-color": "primary"}),
            "light_background": ColorInput(attrs={"data-appearance-color": "light-bg"}),
            "light_surface": ColorInput(attrs={"data-appearance-color": "light-surface"}),
            "dark_background": ColorInput(attrs={"data-appearance-color": "dark-bg"}),
            "dark_surface": ColorInput(attrs={"data-appearance-color": "dark-surface"}),
            "base_font_size": forms.NumberInput(attrs={"min": 15, "max": 22, "step": 1}),
            "persian_font_size": forms.NumberInput(attrs={"min": 16, "max": 24, "step": 1}),
            "content_width": forms.NumberInput(attrs={"min": 1080, "max": 1800, "step": 20}),
            "page_gutter": forms.NumberInput(attrs={"min": 16, "max": 72, "step": 2}),
            "header_height": forms.NumberInput(attrs={"min": 64, "max": 96, "step": 2}),
            "section_spacing": forms.NumberInput(attrs={"min": 40, "max": 120, "step": 4}),
            "card_radius": forms.NumberInput(attrs={"min": 0, "max": 28, "step": 1}),
            "button_radius": forms.NumberInput(attrs={"min": 0, "max": 28, "step": 1}),
        }


class StudioProductSetupForm(forms.ModelForm):
    class Meta:
        model = GarmentStudioProfile
        fields = [
            "is_enabled",
            "garment_type",
            "default_fabric",
            "front_reference",
            "back_reference",
            "left_sleeve_reference",
            "right_sleeve_reference",
            "model_file",
            "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["default_fabric"].queryset = FabricOption.objects.filter(is_active=True).order_by("sort_order", "name")
        self.fields["model_file"].help_text = "GLB recommended. Maximum 40 MB. This will be used by the real 3D viewer."

    def _clean_reference(self, field_name):
        upload = self.cleaned_data.get(field_name)
        if not upload:
            return upload
        # Existing FieldFile objects have no content_type/size in the same way as new uploads.
        if hasattr(upload, "content_type"):
            validate_uploaded_image(upload, max_bytes=12 * 1024 * 1024, max_width=10000, max_height=10000)
        return upload

    def clean_front_reference(self):
        return self._clean_reference("front_reference")

    def clean_back_reference(self):
        return self._clean_reference("back_reference")

    def clean_left_sleeve_reference(self):
        return self._clean_reference("left_sleeve_reference")

    def clean_right_sleeve_reference(self):
        return self._clean_reference("right_sleeve_reference")

    def clean_model_file(self):
        upload = self.cleaned_data.get("model_file")
        if not upload or not hasattr(upload, "size"):
            return upload
        if upload.size > 40 * 1024 * 1024:
            raise forms.ValidationError("3D model must be 40 MB or smaller.")
        name = (upload.name or "").lower()
        if not (name.endswith(".glb") or name.endswith(".gltf")):
            raise forms.ValidationError("Use a GLB or GLTF garment model.")
        return upload
