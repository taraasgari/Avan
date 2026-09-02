from django import forms

from apps.catalog.models import Category, Product
from apps.growth.security import validate_uploaded_image

from .models import Collection, MediaAsset, SeoPage


class ProductContentForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name_en", "name_fa", "description_en", "description_fa",
            "seo_title_en", "seo_title_fa", "seo_description_en", "seo_description_fa",
        ]
        widgets = {
            "description_en": forms.Textarea(attrs={"rows": 5}),
            "description_fa": forms.Textarea(attrs={"rows": 5, "dir": "rtl"}),
            "seo_description_en": forms.Textarea(attrs={"rows": 3}),
            "seo_description_fa": forms.Textarea(attrs={"rows": 3, "dir": "rtl"}),
        }


class CategoryContentForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = [
            "name_en", "name_fa", "description_en", "description_fa",
            "seo_title_en", "seo_title_fa", "seo_description_en", "seo_description_fa",
        ]
        widgets = {
            "description_en": forms.Textarea(attrs={"rows": 4}),
            "description_fa": forms.Textarea(attrs={"rows": 4, "dir": "rtl"}),
            "seo_description_en": forms.Textarea(attrs={"rows": 3}),
            "seo_description_fa": forms.Textarea(attrs={"rows": 3, "dir": "rtl"}),
        }


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = [
            "slug", "name_en", "name_fa", "description_en", "description_fa",
            "hero", "is_active", "is_featured", "sort_order", "starts_at", "ends_at",
        ]
        widgets = {
            "description_en": forms.Textarea(attrs={"rows": 4}),
            "description_fa": forms.Textarea(attrs={"rows": 4, "dir": "rtl"}),
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class MediaAssetForm(forms.ModelForm):
    class Meta:
        model = MediaAsset
        fields = ["title", "file", "kind", "alt_en", "alt_fa"]

    def clean_file(self):
        upload = self.cleaned_data["file"]
        return validate_uploaded_image(upload, max_bytes=12 * 1024 * 1024, max_width=10000, max_height=10000)


class SeoPageForm(forms.ModelForm):
    class Meta:
        model = SeoPage
        fields = [
            "path", "title_en", "title_fa", "description_en", "description_fa",
            "canonical_path", "noindex", "json_ld",
        ]
        widgets = {"json_ld": forms.Textarea(attrs={"rows": 7, "spellcheck": "false"})}

    def clean_path(self):
        value = (self.cleaned_data.get("path") or "").strip()
        if not value.startswith("/"):
            value = "/" + value
        return value

    def clean_canonical_path(self):
        value = (self.cleaned_data.get("canonical_path") or "").strip()
        if value and not value.startswith("/"):
            value = "/" + value
        return value


class BulkCatalogForm(forms.Form):
    file = forms.FileField(help_text="UTF-8 CSV, maximum 5 MB")
    mode = forms.ChoiceField(choices=[("validate", "Validate only"), ("apply", "Apply import")])

    def clean_file(self):
        file = self.cleaned_data["file"]
        if file.size > 5 * 1024 * 1024:
            raise forms.ValidationError("CSV is larger than 5 MB.")
        if not file.name.lower().endswith(".csv"):
            raise forms.ValidationError("Upload a .csv file.")
        return file
