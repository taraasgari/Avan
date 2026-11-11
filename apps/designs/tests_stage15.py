from io import BytesIO

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.catalog.models import Category, Color, Product, ProductVariant, Size
from .models import FabricOption, StudioFont, StudioSettings
from .validators import validate_design_data


class Studio15ValidatorTests(TestCase):
    def test_stage20_five_surface_payload_and_typography_fields(self):
        data = validate_design_data({
            "version": 2,
            "coordinateSpace": "garment-stage-v2",
            "garment": {"fabric": "jersey", "garmentType": "tee", "colorHex": "#111111"},
            "sides": {
                "left_sleeve": [{
                    "id": "x",
                    "type": "text",
                    "text": "سلام AVAN",
                    "fontFamily": "Tahoma",
                    "fontId": "1",
                    "letterSpacing": 2,
                    "lineHeight": 1.4,
                    "size": 64,
                    "weight": 900,
                    "flipX": True,
                    "locked": True,
                }],
                "neck_label": [{
                    "id": "neck",
                    "type": "text",
                    "text": "AVAN",
                    "x": 50,
                    "y": 50,
                }],
            },
        })
        self.assertEqual(data["version"], 2)
        self.assertEqual(data["coordinateSpace"], "garment-stage-v2")
        self.assertIn("right_sleeve", data["sides"])
        self.assertIn("neck_label", data["sides"])
        layer = data["sides"]["left_sleeve"][0]
        self.assertEqual(layer["text"], "سلام AVAN")
        self.assertEqual(layer["size"], 64)
        self.assertEqual(layer["weight"], 900)
        self.assertEqual(layer["lineHeight"], 1.4)
        self.assertTrue(layer["flipX"])
        self.assertTrue(layer["locked"])

    def test_legacy_font_aliases_are_migrated(self):
        data = validate_design_data({
            "version": 2,
            "sides": {
                "front": [{
                    "id": "legacy",
                    "type": "text",
                    "text": "OLD",
                    "fontSize": 72,
                    "fontWeight": "800",
                }],
            },
        })
        layer = data["sides"]["front"][0]
        self.assertEqual(layer["size"], 72)
        self.assertEqual(layer["weight"], 800)
        self.assertNotIn("fontSize", layer)
        self.assertNotIn("fontWeight", layer)


class Studio15PageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="studio15", password="pass12345")
        cat = Category.objects.create(name="Tops", slug="tops")
        self.product = Product.objects.create(
            name="AVAN Tee",
            slug="avan-tee",
            category=cat,
            base_price=100000,
            product_type=Product.ProductType.CUSTOMIZABLE,
            is_active=True,
        )
        color = Color.objects.create(name="Black", slug="black", hex_code="#111111")
        size = Size.objects.create(name="M")
        ProductVariant.objects.create(
            product=self.product,
            color=color,
            size=size,
            sku="TEE-BLK-M",
            stock=5,
            is_active=True,
        )

    def test_studio_contains_stage20_editor_controls(self):
        response = self.client.get("/design/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AVAN / STUDIO")
        self.assertContains(response, "data-garment-stage")
        self.assertContains(response, "data-view-tabs")
        self.assertContains(response, "data-add-text")
        self.assertContains(response, "data-layers-list")
        self.assertContains(response, "data-prop-rotation")

    def test_owner_mode_context_is_superuser_only(self):
        self.client.force_login(self.user)
        response = self.client.get("/design/")
        self.assertFalse(response.context["studio_owner_mode"])

        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save(update_fields=["is_staff", "is_superuser"])
        response = self.client.get("/design/")
        self.assertTrue(response.context["studio_owner_mode"])

    def test_private_sticker_upload(self):
        self.client.force_login(self.user)
        image = Image.new("RGB", (24, 24), "white")
        buffer = BytesIO()
        image.save(buffer, "PNG")
        upload = SimpleUploadedFile("mine.png", buffer.getvalue(), content_type="image/png")
        response = self.client.post("/api/designs/assets/", {"image": upload, "kind": "sticker"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["kind"], "sticker")

    def test_seeded_configuration_exists(self):
        self.assertTrue(FabricOption.objects.exists())
        self.assertTrue(StudioFont.objects.exists())
        self.assertTrue(StudioSettings.load().ai_enabled)
