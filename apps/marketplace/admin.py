from django.contrib import admin, messages

from .models import CreatorEarning, CreatorWallet, MarketplaceSettings, PayoutRequest
from .services import approve_payout, mark_payout_paid, reject_payout


@admin.register(MarketplaceSettings)
class MarketplaceSettingsAdmin(admin.ModelAdmin):
    list_display = ("creator_pricing_enabled", "commission_percent", "minimum_payout_amount", "points_redemption_cost", "points_coupon_value", "updated_at")

    def has_add_permission(self, request):
        return not MarketplaceSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CreatorWallet)
class CreatorWalletAdmin(admin.ModelAdmin):
    list_display = ("creator", "available_balance", "pending_payout", "total_earned", "total_paid", "updated_at")
    search_fields = ("creator__username", "creator__email", "creator__display_name")
    readonly_fields = ("available_balance", "pending_payout", "total_earned", "total_paid", "updated_at")


@admin.register(CreatorEarning)
class CreatorEarningAdmin(admin.ModelAdmin):
    list_display = ("creator", "creator_amount", "gross_design_fee", "platform_commission", "order_item", "created_at")
    search_fields = ("creator__username", "design_id_snapshot", "order_item__order__number")
    readonly_fields = ("creator", "order_item", "design", "design_id_snapshot", "gross_design_fee", "platform_commission", "creator_amount", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.action(description="Approve selected payout requests")
def approve_selected(modeladmin, request, queryset):
    count = 0
    for payout in queryset:
        _, changed = approve_payout(payout)
        count += int(changed)
    modeladmin.message_user(request, f"Approved {count} payout request(s).", messages.SUCCESS)


@admin.action(description="Mark selected approved payouts as paid")
def paid_selected(modeladmin, request, queryset):
    count = 0
    for payout in queryset:
        try:
            _, changed = mark_payout_paid(payout)
            count += int(changed)
        except ValueError as exc:
            modeladmin.message_user(request, str(exc), messages.ERROR)
    modeladmin.message_user(request, f"Marked {count} payout request(s) paid.", messages.SUCCESS)


@admin.action(description="Reject selected payout requests and release balance")
def reject_selected(modeladmin, request, queryset):
    count = 0
    for payout in queryset:
        _, changed = reject_payout(payout)
        count += int(changed)
    modeladmin.message_user(request, f"Rejected {count} payout request(s).", messages.SUCCESS)


@admin.register(PayoutRequest)
class PayoutRequestAdmin(admin.ModelAdmin):
    list_display = ("creator", "amount", "status", "requested_at", "reviewed_at", "paid_at")
    list_filter = ("status", "requested_at")
    search_fields = ("creator__username", "creator__email")
    readonly_fields = ("creator", "amount", "status", "creator_note", "requested_at", "reviewed_at", "paid_at")
    actions = [approve_selected, paid_selected, reject_selected]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
