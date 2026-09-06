from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from apps.core.context_processors import brand
from apps.owner.models import SiteAppearance


User = get_user_model()


class SiteAppearanceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="stage14-owner",
            email="owner@example.com",
            password="StrongPass123!",
        )
        self.customer = User.objects.create_user(
            username="stage14-customer",
            password="StrongPass123!",
        )

    def test_safe_defaults(self):
        appearance = SiteAppearance.load()
        self.assertEqual(appearance.primary_color, "#D50000")
        self.assertEqual(appearance.base_font_size, 17)
        self.assertEqual(appearance.persian_font_size, 18)
        self.assertTrue(appearance.card_shadow)

    def test_visual_editor_is_superuser_only(self):
        self.client.force_login(self.customer)
        response = self.client.get("/owner/appearance/")
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.owner)
        response = self.client.get("/owner/appearance/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-appearance-editor")

    def test_owner_can_publish_appearance(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            "/owner/appearance/",
            {
                "action": "save",
                "primary_color": "#B80000",
                "light_background": "#FFFFFF",
                "light_surface": "#F3F3F3",
                "dark_background": "#0B0B0D",
                "dark_surface": "#18181A",
                "base_font_size": "18",
                "persian_font_size": "20",
                "content_width": "1500",
                "page_gutter": "36",
                "header_height": "78",
                "section_spacing": "80",
                "card_radius": "16",
                "button_radius": "10",
                "card_shadow": "on",
            },
        )
        self.assertRedirects(response, "/owner/appearance/")
        appearance = SiteAppearance.load()
        self.assertEqual(appearance.primary_color, "#B80000")
        self.assertEqual(appearance.persian_font_size, 20)
        self.assertEqual(appearance.card_radius, 16)

    def test_storefront_context_uses_saved_appearance(self):
        appearance = SiteAppearance.load()
        appearance.primary_color = "#AA0011"
        appearance.save()

        request = RequestFactory().get("/")
        request.user = self.customer
        context = brand(request)
        self.assertEqual(context["AVAN_PRIMARY_COLOR"], "#AA0011")
        self.assertEqual(context["AVAN_APPEARANCE"]["primary_color"], "#AA0011")
