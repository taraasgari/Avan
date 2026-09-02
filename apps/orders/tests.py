import uuid
from django.test import TestCase
from apps.cart.models import Cart, CartItem
from apps.catalog.models import Category, Color, Product, ProductVariant, Size
from apps.orders.models import Order, StockReservation
from apps.orders.services import confirm_payment, place_order


class CheckoutFlowTest(TestCase):
    def setUp(self):
        category = Category.objects.create(name="T-Shirts", slug="t-shirts")
        color = Color.objects.create(name="Black", slug="black")
        size = Size.objects.create(name="L")
        product = Product.objects.create(name="Oversized Tee", slug="oversized-tee", category=category, base_price=1000000)
        self.variant = ProductVariant.objects.create(product=product, color=color, size=size, sku="TEE-BLK-L", stock=5)
        self.cart = Cart.objects.create()
        CartItem.objects.create(cart=self.cart, variant=self.variant, quantity=2)
        self.checkout_data = {
            "customer_name": "Test User",
            "phone": "09120000000",
            "province": "Tehran",
            "city": "Tehran",
            "address": "Test address",
        }

    def test_place_order_reserves_but_does_not_decrement_stock(self):
        order, created = place_order(cart=self.cart, checkout_data=self.checkout_data)
        self.assertTrue(created)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 5)
        self.assertEqual(order.status, Order.Status.PENDING_PAYMENT)
        self.assertEqual(order.reservations.get().status, StockReservation.Status.ACTIVE)

    def test_payment_consumes_reservation_and_stock(self):
        order, _ = place_order(cart=self.cart, checkout_data=self.checkout_data)
        payment = order.payment_attempts.get()
        confirm_payment(order, payment, external_reference="TEST")
        self.variant.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(self.variant.stock, 3)
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(order.reservations.get().status, StockReservation.Status.CONSUMED)

    def test_idempotency_key_does_not_duplicate_order(self):
        key = uuid.uuid4()
        order1, created1 = place_order(cart=self.cart, checkout_data=self.checkout_data, idempotency_key=key)
        order2, created2 = place_order(cart=self.cart, checkout_data=self.checkout_data, idempotency_key=key)
        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(order1.pk, order2.pk)
