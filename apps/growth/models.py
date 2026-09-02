from django.conf import settings
from django.db import models


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preference",
    )
    order_updates = models.BooleanField(default=True)
    social_activity = models.BooleanField(default=True)
    rewards = models.BooleanField(default=True)
    product_and_drop_news = models.BooleanField(default=True)
    security_alerts = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification preferences — {self.user}"


class ContentReport(models.Model):
    class TargetType(models.TextChoices):
        DESIGN = "design", "Design"
        CREATOR = "creator", "Creator"

    class Reason(models.TextChoices):
        SPAM = "spam", "Spam"
        COPYRIGHT = "copyright", "Copyright"
        ABUSE = "abuse", "Abusive content"
        MISLEADING = "misleading", "Misleading"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        REVIEWING = "reviewing", "Reviewing"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="content_reports",
    )
    target_type = models.CharField(max_length=20, choices=TargetType.choices)
    target_id = models.CharField(max_length=100)
    target_label = models.CharField(max_length=220, blank=True)
    reason = models.CharField(max_length=30, choices=Reason.choices)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_content_reports",
    )
    resolution_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self):
        return f"{self.target_type}:{self.target_id} — {self.reason}"


class SecurityEvent(models.Model):
    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        HIGH = "high", "High"

    kind = models.CharField(max_length=60)
    severity = models.CharField(max_length=12, choices=Severity.choices, default=Severity.INFO)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_events",
    )
    ip_hash = models.CharField(max_length=64, blank=True)
    path = models.CharField(max_length=500, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["kind", "-created_at"]),
            models.Index(fields=["severity", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.kind} ({self.severity})"


class SeoRedirect(models.Model):
    old_path = models.CharField(max_length=500, unique=True)
    new_path = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)
    hit_count = models.PositiveBigIntegerField(default=0)
    last_hit_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["old_path"]

    def __str__(self):
        return f"{self.old_path} → {self.new_path}"
