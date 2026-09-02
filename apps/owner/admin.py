from django.contrib import admin

from .models import OwnerSettings


@admin.register(OwnerSettings)
class OwnerSettingsAdmin(admin.ModelAdmin):
    list_display = ("store_name", "support_email", "support_phone", "low_stock_threshold", "updated_at")
