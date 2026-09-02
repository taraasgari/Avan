from django.contrib import admin
from .models import Coupon, CouponRedemption


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "value", "is_active", "starts_at", "ends_at")
    list_filter = ("discount_type", "is_active")
    search_fields = ("code",)


@admin.register(CouponRedemption)
class CouponRedemptionAdmin(admin.ModelAdmin):
    list_display = ("coupon", "user", "order", "redeemed_at")
    readonly_fields = ("redeemed_at",)
