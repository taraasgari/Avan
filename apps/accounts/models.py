import uuid
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


class User(AbstractUser):
    display_name = models.CharField(max_length=80, blank=True)
    public_profile_enabled = models.BooleanField(default=False)
    bio = models.CharField(max_length=280, blank=True)
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", blank=True, null=True)

    def __str__(self):
        return self.display_name or self.username


class CreatorFollow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_creators",
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="creator_followers",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "creator"],
                name="uniq_creator_follow",
            ),
            models.CheckConstraint(
                condition=~models.Q(follower=models.F("creator")),
                name="prevent_self_follow",
            ),
        ]

    def __str__(self):
        return f"{self.follower} → {self.creator}"

class SupportTicket(models.Model):
    class Category(models.TextChoices):
        ORDER = "order", "Order"
        PRODUCT = "product", "Product"
        PAYMENT = "payment", "Payment"
        RETURN = "return", "Return / Refund"
        DESIGN = "design", "Design Studio"
        ACCOUNT = "account", "Account"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        WAITING_SUPPORT = "waiting_support", "Waiting for support"
        WAITING_USER = "waiting_user", "Waiting for user"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_tickets",
    )
    category = models.CharField(max_length=24, choices=Category.choices, default=Category.OTHER)
    subject = models.CharField(max_length=180)
    order_number = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.WAITING_SUPPORT)
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.NORMAL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_message_at", "-id"]
        indexes = [
            models.Index(fields=["status", "-last_message_at"], name="acct_support_status_idx"),
            models.Index(fields=["user", "-last_message_at"], name="acct_support_user_idx"),
        ]

    def __str__(self):
        return f"{self.reference} — {self.subject}"


class SupportMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_messages",
    )
    body = models.TextField(max_length=5000)
    is_staff_reply = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.ticket_id} / {self.created_at:%Y-%m-%d %H:%M}"

