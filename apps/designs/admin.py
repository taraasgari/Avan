from django.contrib import admin

from .models import (
    Design, DesignAsset, DesignLike, DesignSave, FabricOption, GarmentMockup,
    GarmentStudioProfile, StickerAsset, StickerCategory, StudioFont, StudioSettings,
)

@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    list_display=("title","owner","base_product","base_color","status","visibility","is_for_sale","sale_price","allow_remix","published_at","updated_at")
    list_filter=("status","visibility","is_for_sale","allow_remix","base_product")
    search_fields=("title","owner__username","owner__display_name","base_product__name")
    readonly_fields=("id","created_at","updated_at","published_at")

@admin.register(DesignAsset)
class DesignAssetAdmin(admin.ModelAdmin):
    list_display=("id","owner","kind","original_name","mime_type","created_at")
    list_filter=("kind",)
    search_fields=("owner__username","original_name","source_prompt")

@admin.register(GarmentMockup)
class GarmentMockupAdmin(admin.ModelAdmin):
    list_display=("product","color","side","print_x","print_y","print_width","print_height")
    list_filter=("side","product","color")

@admin.register(FabricOption)
class FabricOptionAdmin(admin.ModelAdmin):
    list_display=("name","name_fa","slug","roughness","weave_strength","sheen","is_active")
    list_editable=("is_active",)

@admin.register(GarmentStudioProfile)
class GarmentStudioProfileAdmin(admin.ModelAdmin):
    list_display=("product","garment_type","default_fabric","is_enabled")
    list_editable=("is_enabled",)

@admin.register(StickerCategory)
class StickerCategoryAdmin(admin.ModelAdmin):
    list_display=("name","name_fa","slug","is_active","sort_order")
    list_editable=("is_active","sort_order")

@admin.register(StickerAsset)
class StickerAssetAdmin(admin.ModelAdmin):
    list_display=("title","category","is_active","sort_order","created_at")
    list_filter=("category","is_active")
    list_editable=("is_active","sort_order")

@admin.register(StudioFont)
class StudioFontAdmin(admin.ModelAdmin):
    list_display=("name","language_support","family_name","is_active","sort_order")
    list_editable=("is_active","sort_order")

@admin.register(StudioSettings)
class StudioSettingsAdmin(admin.ModelAdmin):
    list_display=("singleton_key","ai_enabled","ai_model","allow_user_stickers","inspiration_enabled","max_upload_mb","updated_at")

admin.site.register(DesignLike)
admin.site.register(DesignSave)
