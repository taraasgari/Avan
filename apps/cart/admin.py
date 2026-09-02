from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("variant", "design", "design_fee", "design_snapshot", "created_at", "updated_at")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("token", "user", "status", "coupon", "updated_at")
    list_filter = ("status",)
    search_fields = ("token", "user__username", "user__email")
    readonly_fields = ("token", "created_at", "updated_at")
    inlines = [CartItemInline]
