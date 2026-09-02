from django.contrib import admin
from .models import Coupon, CouponRedemption


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "value", "assigned_user", "is_active", "starts_at", "ends_at")
    list_filter = ("discount_type", "is_active")
    search_fields = ("code", "assigned_user__username", "assigned_user__email")


@admin.register(CouponRedemption)
class CouponRedemptionAdmin(admin.ModelAdmin):
    list_display = ("coupon", "user", "order", "redeemed_at")
    readonly_fields = ("redeemed_at",)
