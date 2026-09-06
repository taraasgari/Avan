from django.contrib import admin

from .models import OwnerSettings, SiteAppearance


@admin.register(OwnerSettings)
class OwnerSettingsAdmin(admin.ModelAdmin):
    list_display = ("store_name", "support_email", "support_phone", "low_stock_threshold", "updated_at")


@admin.register(SiteAppearance)
class SiteAppearanceAdmin(admin.ModelAdmin):
    list_display = ("primary_color", "base_font_size", "persian_font_size", "content_width", "updated_at")
