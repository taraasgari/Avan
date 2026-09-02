import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from .models import OwnerAuditEvent, StaffAccess
from .permissions import staff_can_access_path


class LaunchOpsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_superuser(username="owner13", email="owner13@example.com", password="Strong-pass-13")
        self.staff = User.objects.create_user(username="staff13", password="Strong-pass-13", is_staff=True)

    def test_health_endpoints(self):
        self.assertEqual(self.client.get("/_health/live/").status_code, 200)
        self.assertEqual(self.client.get("/_health/ready/").status_code, 200)

    def test_metrics_is_hidden_without_token(self):
        self.assertEqual(self.client.get("/_metrics/").status_code, 404)

    @patch.dict(os.environ, {"AVAN_METRICS_TOKEN": "x" * 40}, clear=False)
    def test_metrics_accepts_header_token(self):
        response = self.client.get("/_metrics/", HTTP_X_AVAN_METRICS_TOKEN="x" * 40)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"avan_up 1", response.content)

    def test_staff_permission_is_section_scoped(self):
        access = StaffAccess.objects.create(user=self.staff, role=StaffAccess.Role.CATALOG, can_manage_catalog=True)
        self.assertTrue(staff_can_access_path(self.staff, "/owner/products/"))
        self.assertFalse(staff_can_access_path(self.staff, "/owner/finance/"))
        self.assertFalse(staff_can_access_path(self.staff, "/owner/staff/"))
        access.can_manage_finance = True
        access.save(update_fields=["can_manage_finance"])
        self.assertTrue(staff_can_access_path(self.staff, "/owner/finance/"))

    def test_owner_write_creates_audit_event(self):
        self.client.force_login(self.owner)
        response = self.client.post("/owner/staff/999999/toggle/")
        self.assertIn(response.status_code, {404, 302})
        self.assertTrue(OwnerAuditEvent.objects.filter(actor=self.owner, method="POST").exists())

    def test_launch_center_superuser_only(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get("/owner/launch/").status_code, 403)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get("/owner/launch/").status_code, 200)
