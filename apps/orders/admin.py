from django.contrib import admin
from .models import Order, OrderItem, StockReservation


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "variant", "product_name", "sku", "color_name", "size_name", "unit_price", "quantity", "line_total",
        "is_customized", "design_id_snapshot", "design_title", "design_owner_name", "design_snapshot",
    )
    can_delete = False


class ReservationInline(admin.TabularInline):
    model = StockReservation
    extra = 0
    readonly_fields = ("variant", "quantity", "status", "expires_at", "created_at")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "customer_name", "status", "total_amount", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("number", "customer_name", "phone", "email")
    readonly_fields = ("number", "idempotency_key", "subtotal", "discount_amount", "shipping_amount", "total_amount", "paid_at", "created_at", "updated_at")
    inlines = [OrderItemInline, ReservationInline]


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = ("order", "variant", "quantity", "status", "expires_at")
    list_filter = ("status",)
