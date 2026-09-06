from django.test import Client, TestCase

from apps.catalog.models import Category, Product


class Stage19SearchAndLocaleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="T-Shirts", slug="tshirts", name_fa="تیشرت")
        self.product = Product.objects.create(
            name="AVAN Black Tee",
            slug="avan-black-tee",
            category=self.category,
            base_price=890000,
            search_tags="مشکی, اورسایز, streetwear, black tee",
        )

    def test_persian_is_default_language(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Content-Language"), "fa")

    def test_live_search_uses_owner_tags(self):
        response = self.client.get("/search/suggest/?q=streetwear")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        items = [item for group in payload["groups"] for item in group["items"]]
        self.assertTrue(any(item["url"] == "/shop/avan-black-tee/" for item in items))

    def test_short_query_returns_no_suggestions(self):
        response = self.client.get("/search/suggest/?q=a")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["groups"], [])
