import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.catalog.models import Product, ProductVariant

from .forms import SizePassportForm
from .models import Outfit, OutfitItem, SizePassport


def _variant_payload(variant):
    image = variant.product.images.first()
    return {
        "id": variant.id,
        "product": variant.product.name,
        "product_slug": variant.product.slug,
        "color_id": variant.color_id,
        "color": variant.color.name,
        "size_id": variant.size_id,
        "size": variant.size.name,
        "price": int(variant.price),
        "stock": variant.available_stock,
        "image": image.image.url if image else None,
    }


@login_required(login_url="/account/login/")
def size_passport(request):
    passport, _ = SizePassport.objects.get_or_create(user=request.user)
    saved = False
    form = SizePassportForm(request.POST or None, instance=passport)

    if request.method == "POST" and form.is_valid():
        form.save()
        saved = True

    return render(
        request,
        "wardrobe/size_passport.html",
        {"form": form, "passport": passport, "saved": saved},
    )


@login_required(login_url="/account/login/")
def outfits(request):
    outfit_list = (
        Outfit.objects.filter(owner=request.user)
        .prefetch_related(
            "items__variant__product__images",
            "items__variant__color",
            "items__variant__size",
        )
        .order_by("-updated_at")
    )
    return render(request, "wardrobe/outfits.html", {"outfits": outfit_list})


@login_required(login_url="/account/login/")
@require_POST
def outfit_create(request):
    title = (request.POST.get("title") or "New Outfit").strip()[:120] or "New Outfit"
    outfit = Outfit.objects.create(owner=request.user, title=title)
    return redirect("wardrobe:outfit-builder", outfit_id=outfit.id)


@login_required(login_url="/account/login/")
def outfit_builder(request, outfit_id):
    outfit = get_object_or_404(
        Outfit.objects.prefetch_related(
            "items__variant__product__images",
            "items__variant__color",
            "items__variant__size",
        ),
        id=outfit_id,
        owner=request.user,
    )

    products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("images", "variants__color", "variants__size")
        .order_by("category__sort_order", "name")
    )

    passport = getattr(request.user, "size_passport", None)
    recommended_size_id = passport.usual_top_size_id if passport else None

    product_cards = []
    for product in products:
        variants = [
            _variant_payload(v)
            for v in product.variants.all()
            if v.is_active and v.available_stock > 0
        ]
        if not variants:
            continue
        image = product.images.first()
        product_cards.append(
            {
                "product": product,
                "image_url": image.image.url if image else None,
                "variants": variants,
            }
        )

    return render(
        request,
        "wardrobe/outfit_builder.html",
        {
            "outfit": outfit,
            "product_cards": product_cards,
            "passport": passport,
            "recommended_size_id": recommended_size_id,
        },
    )


@login_required(login_url="/account/login/")
@require_http_methods(["PATCH"])
def outfit_update(request, outfit_id):
    outfit = get_object_or_404(Outfit, id=outfit_id, owner=request.user)
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON."}, status=400)

    title = str(payload.get("title", "")).strip()[:120]
    if not title:
        return JsonResponse({"detail": "Title is required."}, status=400)

    outfit.title = title
    outfit.save(update_fields=["title", "updated_at"])
    return JsonResponse({"ok": True, "title": outfit.title})


@login_required(login_url="/account/login/")
@require_POST
def outfit_add_item(request, outfit_id):
    outfit = get_object_or_404(Outfit, id=outfit_id, owner=request.user)
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON."}, status=400)

    variant = get_object_or_404(
        ProductVariant.objects.select_related("product", "color", "size"),
        id=payload.get("variant_id"),
        is_active=True,
        product__is_active=True,
    )
    if variant.available_stock <= 0:
        return JsonResponse({"detail": "This variant is out of stock."}, status=409)

    position = payload.get("position") or OutfitItem.Position.OTHER
    valid_positions = {choice[0] for choice in OutfitItem.Position.choices}
    if position not in valid_positions:
        position = OutfitItem.Position.OTHER

    item, created = OutfitItem.objects.get_or_create(
        outfit=outfit,
        variant=variant,
        defaults={"position": position, "sort_order": outfit.items.count()},
    )
    if not created and item.position != position:
        item.position = position
        item.save(update_fields=["position"])

    outfit.save(update_fields=["updated_at"])
    data = _variant_payload(variant)
    data.update({"item_id": item.id, "position": item.position})
    return JsonResponse({"created": created, "item": data})


@login_required(login_url="/account/login/")
@require_http_methods(["DELETE"])
def outfit_remove_item(request, outfit_id, item_id):
    item = get_object_or_404(
        OutfitItem,
        id=item_id,
        outfit_id=outfit_id,
        outfit__owner=request.user,
    )
    outfit = item.outfit
    item.delete()
    outfit.save(update_fields=["updated_at"])
    return JsonResponse({"ok": True})


@login_required(login_url="/account/login/")
@require_POST
def outfit_delete(request, outfit_id):
    outfit = get_object_or_404(Outfit, id=outfit_id, owner=request.user)
    outfit.delete()
    return redirect("wardrobe:outfits")
