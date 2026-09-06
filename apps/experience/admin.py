from django.contrib import admin

from .models import (
    Challenge,
    ChallengeEntry,
    Drop,
    DropItem,
    GameScore,
    RewardTransaction,
    RewardWallet,
    SoloGame,
)


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


@admin.action(description="Mark selected entries as winners and grant configured rewards")
def mark_winners_and_grant(modeladmin, request, queryset):
    granted = 0
    for entry in queryset.select_related("challenge", "user"):
        entry.status = ChallengeEntry.Status.WINNER
        entry.save(update_fields=["status"])
        entry.refresh_from_db(fields=["reward_granted"])
        granted += int(entry.reward_granted)
    modeladmin.message_user(request, f"Winner status updated. Reward bundles granted: {granted}.")


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "is_enabled", "challenge_type", "garment_product", "reward_points", "reward_discount_percent", "reward_subsidy_amount", "starts_at", "ends_at")
    list_filter = ("status", "is_enabled", "challenge_type")
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


@admin.register(SoloGame)
class SoloGameAdmin(admin.ModelAdmin):
    list_display = ("title", "game_type", "is_enabled", "bronze_score", "silver_score", "gold_score", "sort_order")
    fieldsets = (
        ("Game", {"fields": ("title", "title_fa", "slug", "game_type", "description", "description_fa", "is_enabled", "sort_order")}),
        ("Hidden medal thresholds", {"fields": ("bronze_score", "silver_score", "gold_score", "score_cap", "max_score_per_second")}),
        ("Bronze reward", {"fields": ("bronze_points", "bronze_discount_percent", "bronze_subsidy_amount")}),
        ("Silver reward", {"fields": ("silver_points", "silver_discount_percent", "silver_subsidy_amount")}),
        ("Gold reward", {"fields": ("gold_points", "gold_discount_percent", "gold_subsidy_amount")}),
        ("Reward policy", {"fields": ("reward_expiry_days",)}),
    )
    list_filter = ("game_type", "is_enabled")
    search_fields = ("title", "title_fa", "slug")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(GameScore)
class GameScoreAdmin(admin.ModelAdmin):
    list_display = ("game", "user", "score", "reward_tier", "points_awarded", "played_at")
    list_filter = ("game", "reward_tier")
    search_fields = ("user__username", "game__title")
    readonly_fields = ("played_at",)
