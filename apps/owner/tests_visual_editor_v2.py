import io
import json

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from apps.owner.models import PageDesign


User = get_user_model()


class VisualEditorV2Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="visual-v2-owner",
            email="visual-v2@example.com",
            password="StrongPass123!",
        )

    def test_owner_preview_can_be_same_origin_framed(self):
        self.client.force_login(self.owner)
        response = self.client.get("/design/?visual_edit=1&visual_preview=1")
        self.assertNotEqual(response.status_code, 403)
        self.assertEqual(response.headers.get("X-Frame-Options"), "SAMEORIGIN")

    def test_account_preview_is_owner_only_same_origin(self):
        response = self.client.get("/account/?visual_edit=1&visual_preview=1")
        self.assertNotEqual(response.headers.get("X-Frame-Options"), "SAMEORIGIN")

        self.client.force_login(self.owner)
        response = self.client.get("/account/?visual_edit=1&visual_preview=1")
        self.assertEqual(response.headers.get("X-Frame-Options"), "SAMEORIGIN")

    def test_api_accepts_inserted_text_on_account(self):
        self.client.force_login(self.owner)
        payload = {
            "path": "/account/",
            "action": "save",
            "elements": [{
                "kind": "insert",
                "id": "vb-test-element",
                "parent_path": [{"tag": "main", "index": 1}],
                "tag": "p",
                "text": "سلام آوان",
                "styles": {"fontSize": "18px", "color": "#171717"},
                "attrs": {},
            }],
        }
        response = self.client.post(
            "/owner/design/api/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        page = PageDesign.objects.get(page_path="/account/")
        self.assertEqual(page.draft_data["elements"][0]["kind"], "insert")

    def test_image_upload_returns_media_url(self):
        self.client.force_login(self.owner)
        buffer = io.BytesIO()
        Image.new("RGB", (16, 16), "white").save(buffer, format="PNG")
        upload = SimpleUploadedFile("sample.png", buffer.getvalue(), content_type="image/png")
        response = self.client.post("/owner/design/upload/", {"file": upload})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["url"].startswith("/media/"))
