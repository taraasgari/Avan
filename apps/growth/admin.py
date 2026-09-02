from django.contrib import admin

from .models import ContentReport, NotificationPreference, SecurityEvent, SeoRedirect


@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
    list_display = ("id", "target_type", "target_label", "reason", "status", "reporter", "created_at")
    list_filter = ("target_type", "reason", "status")
    search_fields = ("target_id", "target_label", "details", "reporter__username")


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "kind", "severity", "user", "path")
    list_filter = ("severity", "kind")
    search_fields = ("path", "user__username", "ip_hash")
    readonly_fields = ("created_at",)


@admin.register(SeoRedirect)
class SeoRedirectAdmin(admin.ModelAdmin):
    list_display = ("old_path", "new_path", "is_active", "hit_count", "last_hit_at")
    list_filter = ("is_active",)
    search_fields = ("old_path", "new_path")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "order_updates", "social_activity", "rewards", "product_and_drop_news", "security_alerts")
    search_fields = ("user__username", "user__email")
