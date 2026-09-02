from django.contrib import admin

from .models import CatalogImportJob, Collection, CollectionItem, MediaAsset, SeoPage


class CollectionItemInline(admin.TabularInline):
    model = CollectionItem
    extra = 0


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name_en", "slug", "is_active", "is_featured", "sort_order")
    list_filter = ("is_active", "is_featured")
    search_fields = ("name_en", "name_fa", "slug")
    inlines = [CollectionItemInline]


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "created_at", "uploaded_by")
    list_filter = ("kind",)
    search_fields = ("title", "alt_en", "alt_fa", "file")


@admin.register(SeoPage)
class SeoPageAdmin(admin.ModelAdmin):
    list_display = ("path", "title_en", "title_fa", "noindex", "updated_at")
    search_fields = ("path", "title_en", "title_fa")


@admin.register(CatalogImportJob)
class CatalogImportJobAdmin(admin.ModelAdmin):
    list_display = ("file_name", "status", "successful_rows", "total_rows", "created_by", "created_at")
    readonly_fields = ("file_name", "status", "successful_rows", "total_rows", "errors", "created_by", "created_at")
