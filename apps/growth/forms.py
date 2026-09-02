from django import forms

from .models import ContentReport, NotificationPreference, SeoRedirect


class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = ["order_updates", "social_activity", "rewards", "product_and_drop_news", "security_alerts"]


class ContentReportForm(forms.ModelForm):
    class Meta:
        model = ContentReport
        fields = ["reason", "details"]
        widgets = {"details": forms.Textarea(attrs={"rows": 4, "maxlength": 1500})}

    def clean_details(self):
        return (self.cleaned_data.get("details") or "").strip()[:1500]


class SeoRedirectForm(forms.ModelForm):
    class Meta:
        model = SeoRedirect
        fields = ["old_path", "new_path", "is_active"]

    def clean_old_path(self):
        value = (self.cleaned_data.get("old_path") or "").strip()
        if not value.startswith("/"):
            value = "/" + value
        if value.startswith(("/admin/", "/owner/", "/api/")):
            raise forms.ValidationError("Private/system paths cannot be SEO redirects.")
        return value

    def clean_new_path(self):
        value = (self.cleaned_data.get("new_path") or "").strip()
        if not value.startswith("/") or value.startswith("//"):
            raise forms.ValidationError("Use a local absolute path such as /shop/new-slug/.")
        return value

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("old_path") and cleaned.get("old_path") == cleaned.get("new_path"):
            self.add_error("new_path", "Redirect target must be different.")
        return cleaned
