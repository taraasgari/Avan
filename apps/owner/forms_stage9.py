from django import forms

from apps.catalog.models import Category, Color, ProductVariant, Size
from apps.operations.models import ShippingMethod


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug", "sort_order", "is_active"]


class ColorForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = ["name", "slug", "hex_code"]

    def clean_hex_code(self):
        value = (self.cleaned_data.get("hex_code") or "").strip()
        if not value:
            return ""
        if not value.startswith("#"):
            value = f"#{value}"
        if len(value) != 7:
            raise forms.ValidationError("Use a 6-digit HEX value, for example #111111.")
        try:
            int(value[1:], 16)
        except ValueError as exc:
            raise forms.ValidationError("Invalid HEX color.") from exc
        return value.upper()


class SizeForm(forms.ModelForm):
    class Meta:
        model = Size
        fields = ["name", "sort_order"]


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ["color", "size", "sku", "stock", "price_override", "is_active"]

    def clean_stock(self):
        value = self.cleaned_data["stock"]
        if value < 0:
            raise forms.ValidationError("Stock cannot be negative.")
        return value


class ShippingMethodForm(forms.ModelForm):
    class Meta:
        model = ShippingMethod
        fields = [
            "code",
            "name_en",
            "name_fa",
            "base_price",
            "estimated_days_min",
            "estimated_days_max",
            "sort_order",
            "is_active",
        ]

    def clean(self):
        cleaned = super().clean()
        minimum = cleaned.get("estimated_days_min")
        maximum = cleaned.get("estimated_days_max")
        if minimum is not None and maximum is not None and maximum < minimum:
            self.add_error("estimated_days_max", "Maximum delivery days cannot be lower than minimum days.")
        return cleaned
