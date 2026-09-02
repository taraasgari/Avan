from django.contrib import admin
from .models import PaymentAttempt


@admin.register(PaymentAttempt)
class PaymentAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "provider", "amount", "status", "created_at")
    list_filter = ("provider", "status")
    search_fields = ("external_reference", "order__number")
    readonly_fields = ("id", "created_at", "updated_at")
