from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.catalog.models import Category, Color, Product, ProductVariant, Size

from .models import Collection
from .services import import_catalog_csv


class Stage11ContentTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Tees", slug="tees", name_en="Tees", name_fa="تی‌شرت")
        self.product = Product.objects.create(name="Oversized Tee", slug="oversized-tee", category=self.category, base_price=890000, name_en="Oversized Tee", name_fa="تی‌شرت اورسایز")

    def test_localized_catalog_content(self):
        self.assertEqual(self.product.localized_name("fa"), "تی‌شرت اورسایز")
        self.assertEqual(self.product.localized_name("en"), "Oversized Tee")

    def test_public_collection(self):
        collection = Collection.objects.create(slug="new", name_en="New", name_fa="جدید")
        collection.products.add(self.product)
        response = self.client.get("/collections/new/")
        self.assertEqual(response.status_code, 200)

    def test_bulk_import(self):
        content = "sku,product_slug,name_en,name_fa,category_slug,category_en,category_fa,description_en,description_fa,base_price,product_type,color_slug,color_name,color_hex,size,stock,active,featured\nSKU-1,new-tee,New Tee,,tees,Tees,,,,100000,ready,black,Black,#111111,M,7,1,0\n"
        upload = SimpleUploadedFile("catalog.csv", content.encode("utf-8"), content_type="text/csv")
        result = import_catalog_csv(upload, apply=True)
        self.assertTrue(result["applied"])
        self.assertTrue(ProductVariant.objects.filter(sku="SKU-1", stock=7).exists())
