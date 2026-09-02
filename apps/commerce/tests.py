from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.catalog.models import Category, Color, Product, ProductVariant, Size
from apps.operations.models import ShippingMethod
from .models import CommerceSettings, ShippingRule
from .services import shipping_quote


class CommerceShippingTests(TestCase):
    def setUp(self):
        self.method = ShippingMethod.objects.create(code="test", name_en="Test", name_fa="تست", base_price=Decimal("50000"))

    def test_base_shipping(self):
        price, source = shipping_quote(method=self.method, subtotal=Decimal("100000"), province="Tehran", city="Tehran")
        self.assertEqual(price, Decimal("50000"))
        self.assertEqual(source, "base")

    def test_global_free_shipping(self):
        config = CommerceSettings.load()
        config.free_shipping_threshold = Decimal("1000000")
        config.save()
        price, _ = shipping_quote(method=self.method, subtotal=Decimal("1200000"), province="", city="")
        self.assertEqual(price, Decimal("0"))

    def test_specific_rule_override(self):
        ShippingRule.objects.create(method=self.method, name="Tehran", province="Tehran", price_override=Decimal("25000"), priority=1)
        price, source = shipping_quote(method=self.method, subtotal=Decimal("100000"), province="tehran", city="")
        self.assertEqual(price, Decimal("25000"))
        self.assertIn("override", source)
