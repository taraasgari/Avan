import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.cart.models import Cart, CartItem
from apps.catalog.models import Category, Color, Product, ProductVariant, Size
from apps.orders.services import place_order
from .models import Design, DesignLike, DesignSave


User = get_user_model()


class Stage3MarketplaceTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator", password="pass12345", display_name="Creator")
        self.fan = User.objects.create_user(username="fan", password="pass12345", display_name="Fan")
        category = Category.objects.create(name="T-Shirts", slug="t-shirts")
        self.black = Color.objects.create(name="Black", slug="black", hex_code="#111111")
        self.white = Color.objects.create(name="White", slug="white", hex_code="#ffffff")
        self.medium = Size.objects.create(name="M", sort_order=1)
        self.product = Product.objects.create(
            name="AVAN Oversized Tee",
            slug="avan-oversized-tee-stage3",
            category=category,
            base_price=890000,
            product_type=Product.ProductType.CUSTOMIZABLE,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            color=self.black,
            size=self.medium,
            sku="STAGE3-BLACK-M",
            stock=10,
        )
        self.design = Design.objects.create(
            owner=self.creator,
            base_product=self.product,
            base_color=self.black,
            title="Red Samurai",
            status=Design.Status.PUBLISHED,
            visibility=Design.Visibility.PUBLIC,
            allow_remix=True,
            is_for_sale=True,
            design_data={"version": 1, "sides": {"front": [{"id":"a","type":"text","text":"AVAN","x":50,"y":50,"width":40,"rotation":0,"z":1,"fontSize":38,"color":"#111111","fontWeight":"800","align":"center"}], "back": []}},
        )

    def test_like_save_toggle_and_remix(self):
        client = APIClient()
        client.force_authenticate(self.fan)

        response = client.post(f"/api/designs/{self.design.id}/like/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["active"])
        self.assertTrue(DesignLike.objects.filter(user=self.fan, design=self.design).exists())

        response = client.post(f"/api/designs/{self.design.id}/save/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["active"])
        self.assertTrue(DesignSave.objects.filter(user=self.fan, design=self.design).exists())

        response = client.post(f"/api/designs/{self.design.id}/remix/")
        self.assertEqual(response.status_code, 201)
        remix = Design.objects.get(id=response.data["id"])
        self.assertEqual(remix.parent_design_id, self.design.id)
        self.assertEqual(remix.owner, self.fan)
        self.assertEqual(remix.design_data, self.design.design_data)

    def test_public_design_can_be_added_to_guest_cart(self):
        cart = Cart.objects.create()
        client = APIClient()
        response = client.post(
            f"/api/cart/{cart.token}/items/",
            {"variant_id": self.variant.id, "quantity": 1, "design_id": str(self.design.id)},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        item = CartItem.objects.get(cart=cart)
        self.assertEqual(item.design_id, self.design.id)
        self.assertEqual(item.design_snapshot["title"], "Red Samurai")

    def test_order_keeps_immutable_design_snapshot(self):
        cart = Cart.objects.create(user=self.creator)
        snapshot = {
            "id": str(self.design.id),
            "title": self.design.title,
            "owner_name": "Creator",
            "design_data": self.design.design_data,
        }
        CartItem.objects.create(
            cart=cart,
            variant=self.variant,
            design=self.design,
            design_snapshot=snapshot,
            quantity=1,
        )

        order, created = place_order(
            cart=cart,
            checkout_data={
                "customer_name": "Test User",
                "phone": "09120000000",
                "email": "test@example.com",
                "province": "Tehran",
                "city": "Tehran",
                "address": "Test address",
                "postal_code": "",
                "customer_note": "",
            },
            idempotency_key=uuid.uuid4(),
            user=self.creator,
        )
        self.assertTrue(created)
        item = order.items.get()
        self.assertTrue(item.is_customized)
        self.assertEqual(item.design_title, "Red Samurai")

        self.design.title = "Changed Later"
        self.design.design_data = {"version": 1, "sides": {"front": [], "back": []}}
        self.design.save(update_fields=["title", "design_data", "updated_at"])

        item.refresh_from_db()
        self.assertEqual(item.design_title, "Red Samurai")
        self.assertEqual(item.design_snapshot["title"], "Red Samurai")
