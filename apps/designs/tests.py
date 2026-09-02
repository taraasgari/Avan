from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Category, Color, Product, ProductVariant, Size
from .models import Design


class DesignApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="designer", password="test-pass-123")
        category = Category.objects.create(name="T-Shirts", slug="t-shirts")
        color = Color.objects.create(name="Black", slug="black", hex_code="#111111")
        size = Size.objects.create(name="M")
        self.product = Product.objects.create(
            name="Studio Tee",
            slug="studio-tee",
            category=category,
            base_price=900000,
            product_type=Product.ProductType.CUSTOMIZABLE,
        )
        ProductVariant.objects.create(product=self.product, color=color, size=size, sku="STUDIO-BLK-M", stock=5)
        self.color = color
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_create_and_update_design(self):
        response = self.client.post(
            "/api/designs/",
            {
                "title": "My Tee",
                "base_product": self.product.id,
                "base_color": self.color.id,
                "design_data": {"version": 1, "sides": {"front": [], "back": []}},
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        design_id = response.data["id"]
        response = self.client.patch(
            f"/api/designs/{design_id}/",
            {"title": "Updated Tee"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Updated Tee")

    def test_publish_design(self):
        design = Design.objects.create(owner=self.user, base_product=self.product, base_color=self.color)
        response = self.client.post(
            f"/api/designs/{design.id}/publish/",
            {"allow_remix": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        design.refresh_from_db()
        self.assertEqual(design.status, Design.Status.PUBLISHED)
        self.assertTrue(design.allow_remix)
