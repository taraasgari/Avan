import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import signing
from django.test import TestCase
from django.utils import timezone

from apps.coupons.models import Coupon
from apps.experience.models import Challenge, SoloGame


User = get_user_model()


class Stage18PlayTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="player18", password="pass12345")
        self.owner = User.objects.create_superuser(username="owner18", email="owner18@example.com", password="pass12345")
        self.game = SoloGame.objects.create(
            slug="test-hard-game",
            game_type=SoloGame.GameType.RUNNER,
            title="Test Hard Game",
            is_enabled=True,
            bronze_score=50,
            silver_score=100,
            gold_score=9876543,
            bronze_points=73491,
            bronze_discount_percent=5,
            bronze_subsidy_amount=1287654,
            score_cap=5000,
            max_score_per_second=5000,
        )
        self.challenge = Challenge.objects.create(
            title="Private Challenge",
            slug="private-challenge",
            prompt="Make something difficult",
            status=Challenge.Status.PUBLISHED,
            is_enabled=True,
            reward_points=246813,
            reward_discount_percent=33,
            reward_subsidy_amount=975318,
        )

    def test_play_and_challenges_require_login(self):
        response = self.client.get("/play/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/account/login/", response.url)
        response = self.client.get("/challenges/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/account/login/", response.url)

    def test_reward_thresholds_are_not_public(self):
        self.client.force_login(self.user)
        response = self.client.get(f"/play/{self.game.slug}/")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertNotIn(str(self.game.gold_score), body)
        self.assertNotIn(str(self.game.bronze_points), body)
        self.assertNotIn(str(self.game.bronze_subsidy_amount), body)
        response = self.client.get(f"/challenges/{self.challenge.slug}/")
        body = response.content.decode()
        self.assertNotIn(str(self.challenge.reward_points), body)
        self.assertNotIn(str(int(self.challenge.reward_subsidy_amount)), body)

    def test_owner_can_set_hidden_game_rewards(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            f"/owner/play/games/{self.game.id}/quick-update/",
            {
                "bronze_score": 1000,
                "silver_score": 3000,
                "gold_score": 7000,
                "bronze_points": 10,
                "silver_points": 20,
                "gold_points": 40,
                "bronze_discount_percent": 4,
                "silver_discount_percent": 8,
                "gold_discount_percent": 15,
                "bronze_subsidy_amount": 15000,
                "silver_subsidy_amount": 30000,
                "gold_subsidy_amount": 70000,
                "reward_expiry_days": 21,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.game.refresh_from_db()
        self.assertEqual(self.game.gold_score, 7000)
        self.assertEqual(self.game.gold_discount_percent, 15)
        self.assertEqual(int(self.game.gold_subsidy_amount), 70000)

    def test_game_reward_creates_private_coupons_without_returning_values(self):
        self.client.force_login(self.user)
        payload = {
            "game_id": self.game.id,
            "user_id": self.user.id,
            "started_at": int((timezone.now() - timedelta(seconds=5)).timestamp()),
        }
        token = signing.dumps(payload, salt="avan-play-run")
        response = self.client.post(
            f"/play/api/{self.game.slug}/submit/",
            data=json.dumps({"score": 60, "token": token}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["tier"], "bronze")
        self.assertNotIn("discount_percent", data)
        self.assertNotIn("subsidy_amount", data)
        self.assertNotIn("points_awarded", data)
        self.assertTrue(Coupon.objects.filter(assigned_user=self.user, discount_type=Coupon.DiscountType.PERCENT).exists())
        self.assertTrue(Coupon.objects.filter(assigned_user=self.user, discount_type=Coupon.DiscountType.FIXED).exists())
