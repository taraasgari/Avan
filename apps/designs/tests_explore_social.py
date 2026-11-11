from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import CreatorFollow
from apps.catalog.models import Category, Color, Product
from .models import Design


class ExploreSocialFeedTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.viewer = User.objects.create_user(username="viewer", password="test-pass-123")
        self.creator = User.objects.create_user(username="creator", password="test-pass-123", public_profile_enabled=True, display_name="Creator One")
        self.other = User.objects.create_user(username="other", password="test-pass-123", public_profile_enabled=True, display_name="Creator Two")
        self.category = Category.objects.create(name="T-Shirts", name_fa="تیشرت", slug="t-shirts")
        self.color = Color.objects.create(name="Black", slug="black", hex_code="#111111")
        self.product = Product.objects.create(name="Studio Tee", slug="studio-tee-social", category=self.category, base_price=900000, product_type=Product.ProductType.CUSTOMIZABLE)
        self.followed_design = Design.objects.create(owner=self.creator, base_product=self.product, base_color=self.color, title="Followed Design", status=Design.Status.PUBLISHED, visibility=Design.Visibility.PUBLIC, allow_remix=True, published_at=timezone.now())
        self.other_design = Design.objects.create(owner=self.other, base_product=self.product, base_color=self.color, title="Other Design", status=Design.Status.PUBLISHED, visibility=Design.Visibility.PUBLIC, published_at=timezone.now())

    def test_explore_renders_social_layout(self):
        response = self.client.get("/explore/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="social-explore"')
        self.assertContains(response, "کاوش در طرح‌های آوان")
        self.assertContains(response, "پیشنهاد دنبال کردن")
        self.assertContains(response, "Followed Design")
        self.assertContains(response, "Other Design")

    def test_following_feed_filters_to_followed_creators(self):
        CreatorFollow.objects.create(follower=self.viewer, creator=self.creator)
        self.client.force_login(self.viewer)
        response = self.client.get("/explore/?feed=following")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Followed Design")
        self.assertNotContains(response, "Other Design")

    def test_category_filter_keeps_matching_public_designs(self):
        response = self.client.get("/explore/?category=t-shirts")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Followed Design")
        self.assertContains(response, "Other Design")
