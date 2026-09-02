from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings

from .models import NotificationPreference, SeoRedirect


class GrowthStage12Tests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(username="stage12", password="StrongPass!903")

    def test_notification_preferences_require_login_and_save(self):
        response = self.client.get("/account/notification-preferences/")
        self.assertEqual(response.status_code, 302)
        self.client.login(username="stage12", password="StrongPass!903")
        response = self.client.post("/account/notification-preferences/", {
            "order_updates": "on",
            "security_alerts": "on",
        })
        self.assertEqual(response.status_code, 302)
        preference = NotificationPreference.objects.get(user=self.user)
        self.assertTrue(preference.order_updates)
        self.assertFalse(preference.social_activity)

    def test_seo_redirect_is_permanent(self):
        SeoRedirect.objects.create(old_path="/old-page/", new_path="/shop/")
        response = self.client.get("/old-page/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/shop/")
