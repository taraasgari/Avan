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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-starts_at", "-created_at"]

    @property
    def is_open(self):
        if self.status != self.Status.PUBLISHED:
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
