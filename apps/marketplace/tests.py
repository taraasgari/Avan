from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.cart.models import Cart, CartItem
from apps.catalog.models import Category, Color, Product, ProductVariant, Size
from apps.coupons.services import validate_coupon
from apps.designs.models import Design
from apps.experience.models import RewardWallet
from apps.orders.services import confirm_payment, place_order

from .models import CreatorEarning, CreatorWallet, MarketplaceSettings, PayoutRequest
from .services import approve_payout, create_payout_request, mark_payout_paid, redeem_points_for_coupon


User = get_user_model()


class CreatorCommerceTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator", password="pass12345")
        self.buyer = User.objects.create_user(username="buyer", password="pass12345")
        self.other = User.objects.create_user(username="other", password="pass12345")
        category = Category.objects.create(name="T-Shirts", slug="t-shirts")
        color = Color.objects.create(name="Black", slug="black", hex_code="#111111")
        size = Size.objects.create(name="M", sort_order=1)
        self.product = Product.objects.create(
            name="AVAN Creator Tee",
            slug="avan-creator-tee",
            category=category,
            base_price=Decimal("100000"),
            product_type=Product.ProductType.CUSTOMIZABLE,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            color=color,
            size=size,
            sku="CREATOR-M-BLK",
            stock=10,
        )
        self.design = Design.objects.create(
            owner=self.creator,
            base_product=self.product,
            base_color=color,
            title="Creator Mark",
            status=Design.Status.PUBLISHED,
            visibility=Design.Visibility.PUBLIC,
            is_for_sale=True,
            sale_price=Decimal("20000"),
        )
        config = MarketplaceSettings.load()
        config.commission_percent = Decimal("25.00")
        config.minimum_payout_amount = Decimal("50000")
        config.points_redemption_cost = 200
        config.points_coupon_value = Decimal("40000")
        config.save()

    def _paid_creator_order(self):
        cart = Cart.objects.create(user=self.buyer)
        CartItem.objects.create(
            cart=cart,
            variant=self.variant,
            design=self.design,
            design_fee=Decimal("20000"),
            design_snapshot={
                "id": str(self.design.id),
                "title": self.design.title,
                "owner_id": self.creator.id,
                "owner_name": self.creator.username,
                "design_data": {"version": 1, "sides": {"front": [], "back": []}},
            },
        )
        order, created = place_order(
            cart=cart,
            user=self.buyer,
            checkout_data={
                "customer_name": "Buyer",
                "phone": "09120000000",
                "email": "buyer@example.com",
                "province": "Tehran",
                "city": "Tehran",
                "address": "Test address",
                "postal_code": "",
                "customer_note": "",
            },
        )
        self.assertTrue(created)
        item = order.items.get()
        self.assertEqual(item.garment_unit_price, Decimal("100000"))
        self.assertEqual(item.design_fee, Decimal("20000"))
        self.assertEqual(item.unit_price, Decimal("120000"))
        self.assertEqual(item.platform_commission_amount, Decimal("5000"))
        self.assertEqual(item.creator_earning_amount, Decimal("15000"))
        payment = order.payment_attempts.get()
        return confirm_payment(order, payment, external_reference="TEST")

    def test_paid_order_creates_idempotent_creator_earning(self):
        order = self._paid_creator_order()
        self.assertEqual(CreatorEarning.objects.count(), 1)
        earning = CreatorEarning.objects.get()
        self.assertEqual(earning.creator, self.creator)
        self.assertEqual(earning.creator_amount, Decimal("15000"))
        wallet = CreatorWallet.objects.get(creator=self.creator)
        self.assertEqual(wallet.available_balance, Decimal("15000"))
        payment = order.payment_attempts.get()
        confirm_payment(order, payment, external_reference="TEST-AGAIN")
        self.assertEqual(CreatorEarning.objects.count(), 1)
        wallet.refresh_from_db()
        self.assertEqual(wallet.available_balance, Decimal("15000"))

    def test_payout_reserves_then_marks_paid(self):
        wallet = CreatorWallet.objects.create(
            creator=self.creator,
            available_balance=Decimal("100000"),
            total_earned=Decimal("100000"),
        )
        payout = create_payout_request(creator=self.creator, amount="60000")
        wallet.refresh_from_db()
        self.assertEqual(wallet.available_balance, Decimal("40000"))
        self.assertEqual(wallet.pending_payout, Decimal("60000"))
        payout, changed = approve_payout(payout)
        self.assertTrue(changed)
        self.assertEqual(payout.status, PayoutRequest.Status.APPROVED)
        payout, changed = mark_payout_paid(payout)
        self.assertTrue(changed)
        wallet.refresh_from_db()
        self.assertEqual(wallet.pending_payout, Decimal("0"))
        self.assertEqual(wallet.total_paid, Decimal("60000"))

    def test_points_redemption_creates_account_locked_coupon(self):
        RewardWallet.objects.create(user=self.buyer, balance=500)
        coupon = redeem_points_for_coupon(user=self.buyer)
        wallet = RewardWallet.objects.get(user=self.buyer)
        self.assertEqual(wallet.balance, 300)
        self.assertEqual(coupon.assigned_user, self.buyer)
        ok, _ = validate_coupon(coupon, user=self.buyer, subtotal=Decimal("100000"))
        self.assertTrue(ok)
        ok, _ = validate_coupon(coupon, user=self.other, subtotal=Decimal("100000"))
        self.assertFalse(ok)
