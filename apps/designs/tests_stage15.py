from io import BytesIO
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.catalog.models import Category, Color, Product, Size, ProductVariant
from .models import FabricOption, StudioFont, StudioSettings
from .validators import validate_design_data


class Studio15ValidatorTests(TestCase):
    def test_v2_four_surface_payload_and_font_fields(self):
        data=validate_design_data({"garment":{"fabric":"jersey","garmentType":"tee","colorHex":"#111111"},"sides":{"left_sleeve":[{"id":"x","type":"text","text":"سلام AVAN","fontFamily":"Tahoma","fontId":"1","letterSpacing":2}]}})
        self.assertEqual(data["version"],2)
        self.assertIn("right_sleeve",data["sides"])
        self.assertEqual(data["sides"]["left_sleeve"][0]["text"],"سلام AVAN")


class Studio15PageTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user(username="studio15",password="pass12345")
        cat=Category.objects.create(name="Tops",slug="tops")
        self.product=Product.objects.create(name="AVAN Tee",slug="avan-tee",category=cat,base_price=100000,product_type=Product.ProductType.CUSTOMIZABLE,is_active=True)
        color=Color.objects.create(name="Black",slug="black",hex_code="#111111")
        size=Size.objects.create(name="M")
        ProductVariant.objects.create(product=self.product,color=color,size=size,sku="TEE-BLK-M",stock=5,is_active=True)

    def test_studio_contains_3d_controls(self):
        r=self.client.get("/design/")
        self.assertEqual(r.status_code,200)
        self.assertContains(r,"AVAN STUDIO / 3D PRO")
        self.assertContains(r,'data-camera="collar"')
        self.assertContains(r,'data-zone="left_sleeve"')

    def test_owner_mode_is_superuser_only(self):
        self.client.force_login(self.user)
        self.assertNotContains(self.client.get("/design/"),"OWNER STUDIO")
        self.user.is_staff=True;self.user.is_superuser=True;self.user.save(update_fields=["is_staff","is_superuser"])
        self.assertContains(self.client.get("/design/"),"OWNER STUDIO")

    def test_private_sticker_upload(self):
        self.client.force_login(self.user)
        im=Image.new("RGB",(24,24),"white");buf=BytesIO();im.save(buf,"PNG")
        upload=SimpleUploadedFile("mine.png",buf.getvalue(),content_type="image/png")
        r=self.client.post("/api/designs/assets/",{"image":upload,"kind":"sticker"})
        self.assertEqual(r.status_code,201)
        self.assertEqual(r.json()["kind"],"sticker")

    def test_seeded_configuration_exists(self):
        self.assertTrue(FabricOption.objects.exists())
        self.assertTrue(StudioFont.objects.exists())
        self.assertTrue(StudioSettings.load().ai_enabled)
