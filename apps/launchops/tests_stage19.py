from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.launchops.models import StaffAccess
from apps.launchops.permissions import staff_can_access_path


User = get_user_model()


class Stage19StaffPermissionTests(TestCase):
    def test_each_owner_section_can_be_granted_independently(self):
        user = User.objects.create_user(username="agent", password="pass12345", is_staff=True)
        access = StaffAccess.objects.create(user=user, role=StaffAccess.Role.CUSTOM, section_permissions=["support"])
        self.assertTrue(staff_can_access_path(user, "/owner/support/"))
        self.assertFalse(staff_can_access_path(user, "/owner/products/"))
        self.assertFalse(staff_can_access_path(user, "/owner/finance/"))
        access.section_permissions = ["products", "appearance"]
        access.save(update_fields=["section_permissions"])
        self.assertTrue(staff_can_access_path(user, "/owner/products/"))
        self.assertTrue(staff_can_access_path(user, "/owner/appearance/"))
        self.assertFalse(staff_can_access_path(user, "/owner/support/"))
