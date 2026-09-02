from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import Category, Color, Product, Size
from apps.designs.models import Design
from .models import Challenge, ChallengeEntry, RewardWallet
from .services import grant_points


User = get_user_model()


class ExperienceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="creator", password="test-pass-123")
        category = Category.objects.create(name="T-Shirts", slug="t-shirts")
        self.product = Product.objects.create(
            name="Test Tee",
            slug="test-tee",
            category=category,
            base_price=100000,
            product_type=Product.ProductType.CUSTOMIZABLE,
        )
        self.color = Color.objects.create(name="Black", slug="black", hex_code="#000000")
        Size.objects.create(name="L")
        self.design = Design.objects.create(
            owner=self.user,
            base_product=self.product,
            base_color=self.color,
            title="Public Test",
            status=Design.Status.PUBLISHED,
            visibility=Design.Visibility.PUBLIC,
            published_at=timezone.now(),
        )

    def test_reward_reference_is_idempotent(self):
        first, created_first = grant_points(
            user=self.user,
            amount=25,
            reason="Test reward",
            reference="test:reward:1",
        )
        second, created_second = grant_points(
            user=self.user,
            amount=25,
            reason="Test reward",
            reference="test:reward:1",
        )

        self.assertTrue(created_first)
        self.assertFalse(created_second)
        self.assertEqual(first.id, second.id)
        self.assertEqual(RewardWallet.objects.get(user=self.user).balance, 25)

    def test_open_challenge_accepts_public_owned_design(self):
        challenge = Challenge.objects.create(
            title="Red Challenge",
            slug="red-challenge",
            prompt="Make it red",
            status=Challenge.Status.PUBLISHED,
            starts_at=timezone.now() - timedelta(hours=1),
            ends_at=timezone.now() + timedelta(days=2),
            reward_points=100,
        )
        self.client.login(username="creator", password="test-pass-123")
        response = self.client.post(
            f"/challenges/{challenge.slug}/",
            {"design_id": str(self.design.id)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ChallengeEntry.objects.filter(
                challenge=challenge,
                user=self.user,
                design=self.design,
            ).exists()
        )
