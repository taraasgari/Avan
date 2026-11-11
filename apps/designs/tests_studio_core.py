from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Category, Color, Product, ProductVariant, Size
from .models import Design


class StudioCoreRoundTripTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="studio-core",
            password="pass12345",
        )
        category = Category.objects.create(name="Studio Core", slug="studio-core")
        self.color = Color.objects.create(name="Black Core", slug="black-core", hex_code="#111111")
        size = Size.objects.create(name="M Core")
        self.product = Product.objects.create(
            name="Core Tee",
            slug="core-tee",
            category=category,
            base_price=500000,
            product_type=Product.ProductType.CUSTOMIZABLE,
            is_active=True,
        )
        ProductVariant.objects.create(
            product=self.product,
            color=self.color,
            size=size,
            sku="CORE-BLK-M",
            stock=10,
            is_active=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def stage_payload(self):
        return {
            "version": 2,
            "coordinateSpace": "garment-stage-v2",
            "sides": {
                "front": [{
                    "id": "front-text",
                    "type": "text",
                    "text": "AVAN",
                    "x": -8,
                    "y": 112,
                    "width": 135,
                    "size": 77,
                    "weight": 900,
                    "lineHeight": 1.35,
                    "letterSpacing": 4,
                    "color": "#111111",
                    "rotation": 17,
                    "opacity": 0,
                    "flipX": True,
                    "flipY": True,
                    "hidden": True,
                    "locked": True,
                    "z": 12345,
                }],
                "neck_label": [{
                    "id": "neck-ai",
                    "type": "ai",
                    "assetId": "asset-1",
                    "url": "/media/example.png",
                    "name": "AI label",
                    "x": 50,
                    "y": 50,
                    "width": 20,
                    "rotation": 0,
                    "opacity": 0.75,
                    "z": 2,
                }],
            },
        }

    def test_api_round_trip_preserves_stage20_schema(self):
        response = self.client.post(
            "/api/designs/",
            {
                "title": "Core round trip",
                "base_product": self.product.id,
                "base_color": self.color.id,
                "design_data": self.stage_payload(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        saved = response.data["design_data"]

        self.assertEqual(saved["coordinateSpace"], "garment-stage-v2")
        self.assertEqual(len(saved["sides"]["neck_label"]), 1)
        layer = saved["sides"]["front"][0]
        self.assertEqual(layer["x"], -8)
        self.assertEqual(layer["y"], 112)
        self.assertEqual(layer["width"], 135)
        self.assertEqual(layer["size"], 77)
        self.assertEqual(layer["weight"], 900)
        self.assertEqual(layer["lineHeight"], 1.35)
        self.assertEqual(layer["opacity"], 0)
        self.assertTrue(layer["flipX"])
        self.assertTrue(layer["flipY"])
        self.assertTrue(layer["hidden"])
        self.assertTrue(layer["locked"])

        design_id = response.data["id"]
        response = self.client.get(f"/api/designs/{design_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["design_data"], saved)

    def test_public_preview_uses_stage_surface_for_stage_coordinates(self):
        payload = self.stage_payload()
        payload["sides"]["front"][0]["hidden"] = False

        design = Design.objects.create(
            owner=self.user,
            base_product=self.product,
            base_color=self.color,
            title="Public stage design",
            status=Design.Status.PUBLISHED,
            visibility=Design.Visibility.PUBLIC,
            design_data=payload,
        )
        response = self.client.get(f"/explore/{design.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "design-preview__studio-frame")
        self.assertContains(response, "preview-layer--text")
        self.assertContains(response, ">AVAN</span>")

