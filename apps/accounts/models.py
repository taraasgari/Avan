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
