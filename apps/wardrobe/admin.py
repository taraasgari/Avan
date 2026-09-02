from django.contrib import admin

from .models import Outfit, OutfitItem, SizePassport


@admin.register(SizePassport)
class SizePassportAdmin(admin.ModelAdmin):
    list_display = ("user", "usual_top_size", "preferred_fit", "updated_at")
    search_fields = ("user__username", "user__email", "user__display_name")


class OutfitItemInline(admin.TabularInline):
    model = OutfitItem
    extra = 0


@admin.register(Outfit)
class OutfitAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "updated_at")
    search_fields = ("title", "owner__username", "owner__email")
    inlines = [OutfitItemInline]
