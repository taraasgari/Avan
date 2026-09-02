from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.catalog.models import Category, Color, Product, ProductVariant, Size
from apps.marketplace.models import MarketplaceSettings
from apps.marketplace.services import split_design_fee


User = get_user_model()


class OwnerConsoleAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(username="owner", email="owner@example.com", password="StrongPass123!")
        self.user = User.objects.create_user(username="customer", password="StrongPass123!")

    def test_owner_dashboard_requires_superuser(self):
        self.client.force_login(self.user)
        response = self.client.get("/owner/")
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.owner)
        response = self.client.get("/owner/")
        self.assertEqual(response.status_code, 200)

    def test_owner_can_update_warehouse_stock(self):
        category = Category.objects.create(name="T-Shirts", slug="t-shirts")
        color = Color.objects.create(name="Black", slug="black")
        size = Size.objects.create(name="L")
        product = Product.objects.create(
            name="AVAN Tee",
            slug="avan-tee",
            category=category,
            base_price=Decimal("900000"),
        )
        variant = ProductVariant.objects.create(
            product=product,
            color=color,
            size=size,
            sku="AVAN-TEE-BLK-L",
            stock=3,
        )
        self.client.force_login(self.owner)
        response = self.client.post(
            "/owner/warehouse/",
            {"variant_id": variant.id, "stock": "9", "price_override": "", "is_active": "on"},
        )
        self.assertEqual(response.status_code, 302)
        variant.refresh_from_db()
        self.assertEqual(variant.stock, 9)
        self.assertTrue(variant.is_active)


class CreatorPricingSwitchTests(TestCase):
    def test_creator_pricing_is_off_by_default(self):
        config = MarketplaceSettings.load()
        self.assertFalse(config.creator_pricing_enabled)
        commission, creator, rate = split_design_fee(Decimal("100000"))
        self.assertEqual(commission, Decimal("0"))
        self.assertEqual(creator, Decimal("0"))
        self.assertEqual(rate, Decimal("0"))

    def test_creator_pricing_can_be_enabled_later(self):
        config = MarketplaceSettings.load()
        config.creator_pricing_enabled = True
        config.commission_percent = Decimal("20")
        config.save()
        commission, creator, rate = split_design_fee(Decimal("100000"))
        self.assertEqual(commission, Decimal("20000"))
        self.assertEqual(creator, Decimal("80000"))
        self.assertEqual(rate, Decimal("20"))
