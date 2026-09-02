from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.catalog.models import Category, Color, Product, ProductVariant, Size

from .models import Address, InventoryMovement
from .services import adjust_stock


class OperationsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="buyer", password="pass12345")
        self.owner = User.objects.create_superuser(username="owner", password="pass12345", email="owner@example.com")
        category = Category.objects.create(name="Tees", slug="tees")
        product = Product.objects.create(name="Test Tee", slug="test-tee", category=category, base_price=1000)
        color = Color.objects.create(name="Black", slug="black")
        size = Size.objects.create(name="M")
        self.variant = ProductVariant.objects.create(product=product, color=color, size=size, sku="TEE-BLK-M", stock=5)

    def test_address_is_private_to_user(self):
        Address.objects.create(user=self.user, recipient_name="Buyer", phone="1", province="P", city="C", address="A", is_default=True)
        self.client.login(username="buyer", password="pass12345")
        response = self.client.get("/account/addresses/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Buyer")

    def test_inventory_adjustment_is_audited(self):
        movement = adjust_stock(variant_id=self.variant.id, delta=3, kind=InventoryMovement.Kind.RESTOCK, actor=self.owner, note="test")
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 8)
        self.assertEqual(movement.stock_before, 5)
        self.assertEqual(movement.stock_after, 8)

    def test_owner_operations_requires_superuser(self):
        self.client.login(username="buyer", password="pass12345")
        self.assertEqual(self.client.get("/owner/operations/").status_code, 403)
