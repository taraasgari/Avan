from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.catalog.models import Category, Product
from apps.designs.models import GarmentStudioProfile


class ProductStudioWorkflowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_superuser(username="owner16", email="owner16@example.com", password="pass12345")
        self.client.force_login(self.owner)
        self.category = Category.objects.create(name="T-Shirts", slug="t-shirts")

    def test_customizable_product_creates_studio_profile(self):
        response = self.client.post(
            "/owner/products/new/",
            {
                "name": "AVAN Blank Tee",
                "slug": "avan-blank-tee",
                "category": self.category.id,
                "description": "Blank tee for customization",
                "base_price": 890000,
                "product_type": Product.ProductType.CUSTOMIZABLE,
                "is_active": "on",
            },
        )
        product = Product.objects.get(slug="avan-blank-tee")
        self.assertRedirects(response, f"/owner/products/{product.id}/studio/")
        self.assertTrue(GarmentStudioProfile.objects.filter(product=product).exists())

    def test_ready_product_does_not_require_studio_profile(self):
        response = self.client.post(
            "/owner/products/new/",
            {
                "name": "Ready Tee",
                "slug": "ready-tee",
                "category": self.category.id,
                "description": "Ready product",
                "base_price": 500000,
                "product_type": Product.ProductType.READY,
                "is_active": "on",
            },
        )
        product = Product.objects.get(slug="ready-tee")
        self.assertRedirects(response, f"/owner/products/{product.id}/")
        self.assertFalse(GarmentStudioProfile.objects.filter(product=product).exists())

    def test_customizable_filter(self):
        Product.objects.create(name="Ready", slug="ready", category=self.category, base_price=1, product_type="ready")
        Product.objects.create(name="Designable", slug="designable", category=self.category, base_price=1, product_type="customizable")
        response = self.client.get("/owner/products/?state=customizable")
        self.assertContains(response, "Designable")
        self.assertNotContains(response, "ready</small>")


class GarmentChooserTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="T-Shirts", slug="tees")

    def test_only_customizable_products_appear(self):
        Product.objects.create(name="Ready Tee", slug="ready-tee-chooser", category=self.category, base_price=1000, product_type="ready")
        custom = Product.objects.create(name="Studio Tee", slug="studio-tee-chooser", category=self.category, base_price=2000, product_type="customizable")
        GarmentStudioProfile.objects.create(product=custom, is_enabled=True)
        response = self.client.get("/design/garments/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Studio Tee")
        self.assertNotContains(response, "Ready Tee")
        self.assertContains(response, f"/design/?product={custom.id}")
