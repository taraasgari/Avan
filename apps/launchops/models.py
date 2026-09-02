from django.conf import settings
from django.db import models


class StaffAccess(models.Model):
    class Role(models.TextChoices):
        MANAGER = "manager", "Manager"
        CATALOG = "catalog", "Catalog / Content"
        FULFILLMENT = "fulfillment", "Warehouse / Fulfillment"
        SUPPORT = "support", "Customer Support"
        MARKETING = "marketing", "Marketing / Community"
        FINANCE = "finance", "Finance"
        SECURITY = "security", "Security / Audit"
        CUSTOM = "custom", "Custom"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="avan_staff_access",
    )
    role = models.CharField(max_length=24, choices=Role.choices, default=Role.CUSTOM)

    can_view_dashboard = models.BooleanField(default=True)
    can_view_analytics = models.BooleanField(default=False)
    can_manage_catalog = models.BooleanField(default=False)
    can_manage_inventory = models.BooleanField(default=False)
    can_manage_orders = models.BooleanField(default=False)
    can_manage_customers = models.BooleanField(default=False)
    can_manage_designs = models.BooleanField(default=False)
    can_manage_marketing = models.BooleanField(default=False)
    can_manage_finance = models.BooleanField(default=False)
    can_manage_content = models.BooleanField(default=False)
    can_manage_reports = models.BooleanField(default=False)
    can_manage_security = models.BooleanField(default=False)
    can_manage_settings = models.BooleanField(default=False)

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_staff_access_records",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]
        verbose_name = "Staff access"
        verbose_name_plural = "Staff access"

    def __str__(self):
        return f"{self.user} — {self.get_role_display()}"

    @classmethod
    def preset_for_role(cls, role):
        base = {
            "can_view_dashboard": True,
            "can_view_analytics": False,
            "can_manage_catalog": False,
            "can_manage_inventory": False,
            "can_manage_orders": False,
            "can_manage_customers": False,
            "can_manage_designs": False,
            "can_manage_marketing": False,
            "can_manage_finance": False,
            "can_manage_content": False,
            "can_manage_reports": False,
            "can_manage_security": False,
            "can_manage_settings": False,
        }
        presets = {
            cls.Role.MANAGER: {
                "can_view_analytics": True,
                "can_manage_catalog": True,
                "can_manage_inventory": True,
                "can_manage_orders": True,
                "can_manage_customers": True,
                "can_manage_designs": True,
                "can_manage_marketing": True,
                "can_manage_content": True,
                "can_manage_reports": True,
            },
            cls.Role.CATALOG: {
                "can_manage_catalog": True,
                "can_manage_inventory": True,
                "can_manage_content": True,
            },
            cls.Role.FULFILLMENT: {
                "can_manage_inventory": True,
                "can_manage_orders": True,
                "can_manage_customers": True,
            },
            cls.Role.SUPPORT: {
                "can_manage_orders": True,
                "can_manage_customers": True,
                "can_manage_designs": True,
            },
            cls.Role.MARKETING: {
                "can_view_analytics": True,
                "can_manage_designs": True,
                "can_manage_marketing": True,
                "can_manage_content": True,
            },
            cls.Role.FINANCE: {
                "can_view_analytics": True,
                "can_manage_orders": True,
                "can_manage_finance": True,
                "can_manage_reports": True,
            },
            cls.Role.SECURITY: {
                "can_manage_reports": True,
                "can_manage_security": True,
            },
            cls.Role.CUSTOM: {},
        }
        base.update(presets.get(role, {}))
        return base

    def apply_role_preset(self, role=None):
        role = role or self.role
        self.role = role
        for field, value in self.preset_for_role(role).items():
            setattr(self, field, value)


class OwnerAuditEvent(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owner_audit_events",
    )
    action = models.CharField(max_length=80)
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10)
    status_code = models.PositiveSmallIntegerField(default=200)
    request_id = models.CharField(max_length=64, blank=True)
    target = models.CharField(max_length=180, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["-created_at"], name="launch_audit_created_idx"),
            models.Index(fields=["actor", "-created_at"], name="launch_audit_actor_idx"),
            models.Index(fields=["action", "-created_at"], name="launch_audit_action_idx"),
        ]

    def __str__(self):
        return f"{self.action} {self.method} {self.path}"
