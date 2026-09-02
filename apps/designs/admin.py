from django.contrib import admin

from .models import Design, DesignAsset, DesignLike, DesignSave, GarmentMockup


@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    list_display = (
        "title", "owner", "base_product", "base_color", "status", "visibility",
        "is_for_sale", "sale_price", "allow_remix", "published_at", "updated_at",
    )
    list_filter = ("status", "visibility", "is_for_sale", "allow_remix", "base_product")
    search_fields = ("title", "owner__username", "owner__display_name", "base_product__name")
    readonly_fields = ("id", "created_at", "updated_at", "published_at")


@admin.register(DesignAsset)
class DesignAssetAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "original_name", "mime_type", "created_at")
    search_fields = ("owner__username", "original_name")


@admin.register(GarmentMockup)
class GarmentMockupAdmin(admin.ModelAdmin):
    list_display = ("product", "color", "side", "print_x", "print_y", "print_width", "print_height")
    list_filter = ("side", "product", "color")


@admin.register(DesignLike)
class DesignLikeAdmin(admin.ModelAdmin):
    list_display = ("user", "design", "created_at")
    search_fields = ("user__username", "design__title")


@admin.register(DesignSave)
class DesignSaveAdmin(admin.ModelAdmin):
    list_display = ("user", "design", "created_at")
    search_fields = ("user__username", "design__title")
