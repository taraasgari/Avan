from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CreatorFollow, User


@admin.register(User)
class AvanUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "AVAN profile",
            {
                "fields": (
                    "display_name",
                    "bio",
                    "avatar",
                    "public_profile_enabled",
                )
            },
        ),
    )


@admin.register(CreatorFollow)
class CreatorFollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "creator", "created_at")
    search_fields = (
        "follower__username",
        "creator__username",
        "follower__email",
        "creator__email",
    )
    raw_id_fields = ("follower", "creator")
