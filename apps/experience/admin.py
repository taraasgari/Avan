from django.contrib import admin

from .models import (
    Challenge,
    ChallengeEntry,
    Drop,
    DropItem,
    RewardTransaction,
    RewardWallet,
)
from .services import grant_points


class DropItemInline(admin.TabularInline):
    model = DropItem
    extra = 1
    raw_id_fields = ("product", "design")


@admin.register(Drop)
class DropAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "is_featured", "starts_at", "ends_at")
    list_filter = ("status", "is_featured")
    search_fields = ("title", "slug", "subtitle")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [DropItemInline]


@admin.action(description="Mark selected entries as winners and grant configured points")
def mark_winners_and_grant(modeladmin, request, queryset):
    granted = 0
    for entry in queryset.select_related("challenge", "user"):
        entry.status = ChallengeEntry.Status.WINNER
        entry.save(update_fields=["status"])

        if not entry.reward_granted and entry.challenge.reward_points > 0:
            _, created = grant_points(
                user=entry.user,
                amount=entry.challenge.reward_points,
                reason=f"Challenge winner: {entry.challenge.title}",
                reference=f"challenge:{entry.challenge_id}:entry:{entry.id}:winner",
            )
            if created:
                entry.reward_granted = True
                entry.save(update_fields=["reward_granted"])
                granted += 1

    modeladmin.message_user(request, f"Winner status updated. Rewards granted: {granted}.")


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "reward_points", "starts_at", "ends_at")
    list_filter = ("status",)
    search_fields = ("title", "slug", "prompt")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(ChallengeEntry)
class ChallengeEntryAdmin(admin.ModelAdmin):
    list_display = ("challenge", "user", "design", "status", "reward_granted", "created_at")
    list_filter = ("status", "reward_granted", "challenge")
    search_fields = ("user__username", "design__title", "challenge__title")
    autocomplete_fields = ("user", "design", "challenge")
    actions = [mark_winners_and_grant]


@admin.register(RewardWallet)
class RewardWalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "updated_at")
    search_fields = ("user__username", "user__email")


@admin.register(RewardTransaction)
class RewardTransactionAdmin(admin.ModelAdmin):
    list_display = ("wallet", "amount", "reason", "reference", "created_at")
    search_fields = ("wallet__user__username", "reason", "reference")
    readonly_fields = ("created_at",)
