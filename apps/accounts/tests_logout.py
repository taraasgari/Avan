from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AccountLogoutTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="logout-regression-user",
            email="logout-regression@example.test",
            password="A-Strong-Test-Password-2026",
        )

    def test_logout_rejects_get_requests(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

    def test_logout_post_ends_the_session(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, "/")
        self.assertNotIn("_auth_user_id", self.client.session)
