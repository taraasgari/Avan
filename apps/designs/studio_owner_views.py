from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from apps.catalog.models import Product
from apps.growth.security import validate_uploaded_image
from .models import FabricOption, GarmentStudioProfile, StickerAsset, StickerCategory, StudioFont, StudioSettings


def _deny(request):
    if not request.user.is_superuser:
        return JsonResponse({"detail": "Owner access required."}, status=403)
    return None


@login_required(login_url="/account/login/")
@require_POST
def owner_settings(request):
    denied = _deny(request)
    if denied: return denied
    obj = StudioSettings.load()
    obj.ai_enabled = request.POST.get("ai_enabled") == "1"
    obj.allow_user_stickers = request.POST.get("allow_user_stickers") == "1"
    obj.inspiration_enabled = request.POST.get("inspiration_enabled") == "1"
    obj.save()
    return JsonResponse({"ok": True})


@login_required(login_url="/account/login/")
@require_POST
def owner_fabric(request):
    denied = _deny(request)
    if denied: return denied
    name = request.POST.get("name", "").strip()[:80]
    if not name: return JsonResponse({"detail": "Fabric name is required."}, status=400)
    slug = (request.POST.get("slug") or slugify(name) or "fabric")[:90]
    obj, _ = FabricOption.objects.update_or_create(slug=slug, defaults={
        "name": name, "name_fa": request.POST.get("name_fa", "").strip()[:80],
        "roughness": min(1, max(0, float(request.POST.get("roughness", .75)))),
        "weave_strength": min(1, max(0, float(request.POST.get("weave", .08)))),
        "weave_scale": min(400, max(10, float(request.POST.get("scale", 120)))),
        "sheen": min(1, max(0, float(request.POST.get("sheen", .08)))), "is_active": True,
    })
    return JsonResponse({"ok": True, "id": obj.id})


@login_required(login_url="/account/login/")
@require_POST
def owner_font(request):
    denied = _deny(request)
    if denied: return denied
    name = request.POST.get("name", "").strip()[:80]
    if not name: return JsonResponse({"detail": "Font name is required."}, status=400)
    language = request.POST.get("language", "both")
    if language not in StudioFont.LanguageSupport.values: language = "both"
    obj = StudioFont(name=name, family_name=request.POST.get("family_name", "").strip()[:120], language_support=language)
    font_file = request.FILES.get("font_file")
    if font_file:
        ext = font_file.name.rsplit(".", 1)[-1].lower() if "." in font_file.name else ""
        if ext not in {"woff", "woff2"} or font_file.size > 2 * 1024 * 1024:
            return JsonResponse({"detail": "Use a WOFF/WOFF2 font up to 2 MB."}, status=400)
        head = font_file.read(4); font_file.seek(0)
        if head not in {b"wOFF", b"wOF2"}:
            return JsonResponse({"detail": "The uploaded file is not a valid webfont container."}, status=400)
        obj.font_file = font_file
    obj.save()
    return JsonResponse({"ok": True, "id": obj.id})


@login_required(login_url="/account/login/")
@require_POST
def owner_sticker_category(request):
    denied = _deny(request)
    if denied: return denied
    name = request.POST.get("name", "").strip()[:80]
    if not name: return JsonResponse({"detail": "Category name is required."}, status=400)
    slug = (request.POST.get("slug") or slugify(name) or "stickers")[:90]
    obj, _ = StickerCategory.objects.update_or_create(slug=slug, defaults={"name": name, "name_fa": request.POST.get("name_fa", "").strip()[:80], "is_active": True})
    return JsonResponse({"ok": True, "id": obj.id})


@login_required(login_url="/account/login/")
@require_POST
def owner_sticker(request):
    denied = _deny(request)
    if denied: return denied
    category = get_object_or_404(StickerCategory, id=request.POST.get("category"))
    image = request.FILES.get("image")
    if not image: return JsonResponse({"detail": "Sticker image is required."}, status=400)
    try: validate_uploaded_image(image, max_bytes=8 * 1024 * 1024, max_width=5000, max_height=5000)
    except Exception: return JsonResponse({"detail": "Invalid sticker image."}, status=400)
    obj = StickerAsset.objects.create(category=category, title=request.POST.get("title", "Sticker")[:100], title_fa=request.POST.get("title_fa", "")[:100], image=image)
    return JsonResponse({"ok": True, "id": obj.id})


@login_required(login_url="/account/login/")
@require_POST
def owner_garment_profile(request):
    denied = _deny(request)
    if denied: return denied
    product = get_object_or_404(Product, id=request.POST.get("product"))
    garment_type = request.POST.get("garment_type", "tee")
    if garment_type not in GarmentStudioProfile.GarmentType.values: garment_type = "tee"
    fabric = FabricOption.objects.filter(id=request.POST.get("default_fabric")).first()
    obj, _ = GarmentStudioProfile.objects.update_or_create(product=product, defaults={"garment_type": garment_type, "default_fabric": fabric, "is_enabled": True})
    return JsonResponse({"ok": True, "id": obj.id})
