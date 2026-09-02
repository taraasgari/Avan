from django.contrib import admin

from .models import OwnerAuditEvent, StaffAccess


@admin.register(StaffAccess)
class StaffAccessAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "updated_at")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email", "user__display_name")


@admin.register(OwnerAuditEvent)
class OwnerAuditEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "method", "status_code", "path")
    list_filter = ("action", "method", "status_code")
    search_fields = ("actor__username", "path", "request_id", "target")
    readonly_fields = [field.name for field in OwnerAuditEvent._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
