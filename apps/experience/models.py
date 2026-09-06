from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Drop(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, unique=True)
    subtitle = models.CharField(max_length=180, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="drops/%Y/%m/", blank=True, null=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_featured", "-starts_at", "-created_at"]

    @property
    def phase(self):
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return "upcoming"
        if self.ends_at and now > self.ends_at:
            return "ended"
        return "live"

    def __str__(self):
        return self.title


class DropItem(models.Model):
    drop = models.ForeignKey(Drop, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="drop_items",
        null=True,
        blank=True,
    )
    design = models.ForeignKey(
        "designs.Design",
        on_delete=models.CASCADE,
        related_name="drop_items",
        null=True,
        blank=True,
    )
    label = models.CharField(max_length=80, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def clean(self):
        if bool(self.product_id) == bool(self.design_id):
            raise ValidationError("Choose exactly one product or one design.")

    def __str__(self):
        return f"{self.drop} / {self.product or self.design}"


class Challenge(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CLOSED = "closed", "Closed"

    title = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, unique=True)
    prompt = models.CharField(max_length=240)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="challenges/%Y/%m/", blank=True, null=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    reward_points = models.PositiveIntegerField(default=0)
    reward_discount_percent = models.PositiveSmallIntegerField(default=0)
    reward_subsidy_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    reward_expiry_days = models.PositiveIntegerField(default=30)
    is_enabled = models.BooleanField(default=True, help_text="Master visibility switch for the public site.")
    challenge_type = models.CharField(max_length=32, default="theme")
    garment_product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="design_challenges",
    )
    rules = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-starts_at", "-created_at"]

    @property
    def is_open(self):
        if not self.is_enabled or self.status != self.Status.PUBLISHED:
            return False
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True

    @property
    def phase(self):
        if self.status == self.Status.CLOSED:
            return "ended"
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return "upcoming"
        if self.ends_at and now > self.ends_at:
            return "ended"
        return "live" if self.status == self.Status.PUBLISHED else "draft"

    def clean(self):
        super().clean()
        if self.reward_discount_percent > 100:
            raise ValidationError({"reward_discount_percent": "Discount percent cannot exceed 100."})

    def __str__(self):
        return self.title


class ChallengeEntry(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        FINALIST = "finalist", "Finalist"
        WINNER = "winner", "Winner"
        REJECTED = "rejected", "Rejected"

    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="entries")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="challenge_entries",
    )
    design = models.ForeignKey(
        "designs.Design",
        on_delete=models.CASCADE,
        related_name="challenge_entries",
    )
    note = models.CharField(max_length=240, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SUBMITTED)
    reward_granted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["challenge", "user", "design"],
                name="uniq_challenge_user_design",
            )
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status == self.Status.WINNER and not self.reward_granted:
            from .services import grant_challenge_entry_reward
            if grant_challenge_entry_reward(self):
                type(self).objects.filter(pk=self.pk, reward_granted=False).update(reward_granted=True)
                self.reward_granted = True

    def __str__(self):
        return f"{self.challenge} / {self.user} / {self.design}"


class RewardWallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reward_wallet",
    )
    balance = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} / {self.balance} pts"


class RewardTransaction(models.Model):
    wallet = models.ForeignKey(
        RewardWallet,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    amount = models.IntegerField()
    reason = models.CharField(max_length=180)
    reference = models.CharField(max_length=180, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.wallet.user} / {self.amount:+d} / {self.reason}"

class SoloGame(models.Model):
    class GameType(models.TextChoices):
        RUNNER = "runner", "Needle Grid"
        CATCH = "catch", "Pattern Drop"
        MEMORY = "memory", "Signal Forge"
        COLOR = "color", "Tag Strike"

    slug = models.SlugField(max_length=80, unique=True)
    game_type = models.CharField(max_length=16, choices=GameType.choices)
    title = models.CharField(max_length=100)
    title_fa = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=240, blank=True)
    description_fa = models.CharField(max_length=240, blank=True)
    is_enabled = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    bronze_score = models.PositiveIntegerField(default=500)
    silver_score = models.PositiveIntegerField(default=1200)
    gold_score = models.PositiveIntegerField(default=2200)
    bronze_points = models.PositiveIntegerField(default=10)
    silver_points = models.PositiveIntegerField(default=25)
    gold_points = models.PositiveIntegerField(default=50)
    bronze_discount_percent = models.PositiveSmallIntegerField(default=0)
    silver_discount_percent = models.PositiveSmallIntegerField(default=0)
    gold_discount_percent = models.PositiveSmallIntegerField(default=0)
    bronze_subsidy_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    silver_subsidy_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    gold_subsidy_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    reward_expiry_days = models.PositiveIntegerField(default=30)
    score_cap = models.PositiveIntegerField(default=10000)
    max_score_per_second = models.PositiveIntegerField(default=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def reward_tier_for(self, score):
        if score >= self.gold_score:
            return "gold", self.gold_points
        if score >= self.silver_score:
            return "silver", self.silver_points
        if score >= self.bronze_score:
            return "bronze", self.bronze_points
        return "none", 0

    def reward_bundle_for(self, score):
        tier, points = self.reward_tier_for(score)
        if tier == "none":
            return {"tier": tier, "points": 0, "discount_percent": 0, "subsidy_amount": 0}
        return {
            "tier": tier,
            "points": points,
            "discount_percent": getattr(self, f"{tier}_discount_percent"),
            "subsidy_amount": getattr(self, f"{tier}_subsidy_amount"),
        }

    def clean(self):
        super().clean()
        for field_name in ("bronze_discount_percent", "silver_discount_percent", "gold_discount_percent"):
            if getattr(self, field_name, 0) > 100:
                raise ValidationError({field_name: "Discount percent cannot exceed 100."})
        if not (self.bronze_score < self.silver_score < self.gold_score):
            raise ValidationError("Medal score thresholds must increase from bronze to silver to gold.")

    def __str__(self):
        return self.title


class GameScore(models.Model):
    game = models.ForeignKey(SoloGame, on_delete=models.CASCADE, related_name="scores")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="avan_game_scores",
    )
    score = models.PositiveIntegerField()
    reward_tier = models.CharField(max_length=16, default="none")
    points_awarded = models.PositiveIntegerField(default=0)
    played_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score", "played_at"]
        indexes = [
            models.Index(fields=["game", "-score"]),
            models.Index(fields=["user", "-played_at"]),
        ]

    def __str__(self):
        return f"{self.user} / {self.game} / {self.score}"

