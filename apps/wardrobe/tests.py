import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Color, Product, ProductVariant, Size

from .models import Outfit, OutfitItem, SizePassport


User = get_user_model()


class WardrobeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="stylist", password="pass12345")
        category = Category.objects.create(name="T-Shirts", slug="tees")
        color = Color.objects.create(name="Black", slug="black", hex_code="#000000")
        size = Size.objects.create(name="L", sort_order=1)
        product = Product.objects.create(
            name="AVAN Tee",
            slug="avan-tee",
            category=category,
            base_price=100000,
            is_active=True,
        )
        self.variant = ProductVariant.objects.create(
            product=product,
            color=color,
            size=size,
            sku="TEE-BLK-L",
            stock=5,
        )
        self.size = size

    def test_size_passport_is_one_per_user(self):
        passport = SizePassport.objects.create(user=self.user, usual_top_size=self.size)
        self.assertEqual(self.user.size_passport, passport)

    def test_user_can_add_variant_to_own_outfit(self):
        outfit = Outfit.objects.create(owner=self.user, title="Night Fit")
        self.client.login(username="stylist", password="pass12345")
        response = self.client.post(
            reverse("wardrobe:outfit-add-item", kwargs={"outfit_id": outfit.id}),
            data=json.dumps({"variant_id": self.variant.id, "position": "top"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(OutfitItem.objects.filter(outfit=outfit, variant=self.variant).exists())
