from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.cart.models import Cart, CartItem
from apps.catalog.models import Category, Color, Product, ProductVariant, Size
from apps.operations.models import Address, InventoryMovement, Shipment, ShippingMethod
from apps.orders.models import Order


User = get_user_model()


class Stage9OwnerAndCheckoutTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="T-Shirts", slug="t-shirts")
        self.color = Color.objects.create(name="Black", slug="black", hex_code="#111111")
        self.size = Size.objects.create(name="M", sort_order=1)
        self.product = Product.objects.create(
            name="AVAN Tee",
            slug="avan-tee-stage9",
            category=self.category,
            base_price=890000,
            product_type=Product.ProductType.READY,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            color=self.color,
            size=self.size,
            sku="AVAN-S9-BLK-M",
            stock=10,
        )
        self.user = User.objects.create_user(username="buyer9", password="testpass123", email="buyer@example.com")
        self.owner = User.objects.create_superuser(username="owner9", password="testpass123", email="owner@example.com")
        self.method = ShippingMethod.objects.create(
            code="stage9-fast",
            name_en="Fast",
            name_fa="سریع",
            base_price=85000,
            estimated_days_min=1,
            estimated_days_max=2,
        )
        self.address = Address.objects.create(
            user=self.user,
            title="Home",
            recipient_name="Buyer Nine",
            phone="09120000000",
            province="Tehran",
            city="Tehran",
            address="Stage 9 Street",
            postal_code="1234567890",
            is_default=True,
        )

    def test_owner_catalog_and_analytics_are_available(self):
        self.client.login(username="owner9", password="testpass123")
        self.assertEqual(self.client.get("/owner/catalog/").status_code, 200)
        self.assertEqual(self.client.get("/owner/analytics/").status_code, 200)

    def test_variant_manager_records_inventory_history(self):
        self.client.login(username="owner9", password="testpass123")
        response = self.client.post(
            f"/owner/products/{self.product.id}/variants/?edit={self.variant.id}",
            {
                "color": self.color.id,
                "size": self.size.id,
                "sku": self.variant.sku,
                "stock": 16,
                "price_override": "",
                "is_active": "on",
                "action": "save",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 16)
        movement = InventoryMovement.objects.get(variant=self.variant)
        self.assertEqual(movement.delta, 6)
        self.assertEqual(movement.stock_before, 10)
        self.assertEqual(movement.stock_after, 16)

    def test_checkout_uses_saved_address_and_shipping_price(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=1)
        api = APIClient()
        api.force_authenticate(self.user)
        response = api.post(
            f"/api/checkout/{cart.token}/",
            {
                "address_id": self.address.id,
                "shipping_method_id": self.method.id,
                "email": self.user.email,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        order = Order.objects.get(number=response.data["number"])
        self.assertEqual(order.shipping_amount, self.method.base_price)
        self.assertEqual(order.customer_name, self.address.recipient_name)
        self.assertEqual(order.address, self.address.address)
        shipment = Shipment.objects.get(order=order)
        self.assertEqual(shipment.method, self.method)
