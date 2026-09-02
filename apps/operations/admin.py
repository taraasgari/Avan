from django.contrib import admin

from .models import Address, InventoryMovement, ProductionBatch, ReturnRequest, Shipment, ShippingMethod, Supplier


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "city", "is_default", "updated_at")
    search_fields = ("user__username", "recipient_name", "phone", "city")


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ("code", "name_en", "name_fa", "base_price", "is_active", "sort_order")
    list_editable = ("base_price", "is_active", "sort_order")


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "method", "carrier_name", "tracking_code", "updated_at")
    list_filter = ("status", "method")
    search_fields = ("order__number", "tracking_code", "carrier_name")


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "user", "reason", "status", "refund_amount", "created_at")
    list_filter = ("status", "reason")


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ("variant", "kind", "delta", "stock_before", "stock_after", "actor", "created_at")
    list_filter = ("kind",)
    search_fields = ("variant__sku", "variant__product__name", "note")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_name", "phone", "is_active")


@admin.register(ProductionBatch)
class ProductionBatchAdmin(admin.ModelAdmin):
    list_display = ("reference", "product", "supplier", "status", "planned_quantity", "completed_quantity", "expected_at")
    list_filter = ("status",)
