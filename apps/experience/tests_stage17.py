from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.experience.models import Challenge, SoloGame


User = get_user_model()


class PlayVisibilityTests(TestCase):
    def setUp(self):
        self.game = SoloGame.objects.create(
            slug="test-runner",
            game_type=SoloGame.GameType.RUNNER,
            title="Test Runner",
            is_enabled=False,
        )
        self.challenge = Challenge.objects.create(
            title="Hidden Challenge",
            slug="hidden-challenge",
            prompt="Test",
            status=Challenge.Status.PUBLISHED,
            is_enabled=False,
        )

    def test_disabled_game_is_not_public(self):
        self.assertEqual(self.client.get("/play/test-runner/").status_code, 404)

    def test_enabled_game_is_public(self):
        self.game.is_enabled = True
        self.game.save(update_fields=["is_enabled"])
        self.assertEqual(self.client.get("/play/test-runner/").status_code, 200)

    def test_disabled_challenge_is_not_public(self):
        self.assertEqual(self.client.get("/challenges/hidden-challenge/").status_code, 404)

    def test_owner_can_toggle_game_and_challenge(self):
        owner = User.objects.create_superuser(username="owner-stage17", email="owner17@example.com", password="pass12345")
        self.client.force_login(owner)
        response = self.client.post(f"/owner/play/games/{self.game.id}/toggle/", {"enabled": "1"})
        self.assertEqual(response.status_code, 302)
        self.game.refresh_from_db()
        self.assertTrue(self.game.is_enabled)

        response = self.client.post(f"/owner/play/challenges/{self.challenge.id}/toggle/", {"enabled": "1"})
        self.assertEqual(response.status_code, 302)
        self.challenge.refresh_from_db()
        self.assertTrue(self.challenge.is_enabled)
