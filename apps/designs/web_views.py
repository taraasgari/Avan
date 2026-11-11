from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from apps.catalog.models import Product
from apps.marketplace.models import MarketplaceSettings
from .ai import ai_is_configured
from .models import (
    Design, FabricOption, GarmentStudioProfile, StickerAsset, StickerCategory,
    StudioFont, StudioSettings,
)


def _product_payload(product):
    image = product.images.first()
    variants = []
    colors = {}
    sizes = {}

    for variant in product.variants.filter(is_active=True).select_related("color", "size"):
        variants.append({
            "id": variant.id,
            "color_id": variant.color_id,
            "color": variant.color.name,
            "color_hex": variant.color.hex_code or "#dddddd",
            "size_id": variant.size_id,
            "size": variant.size.name,
            "stock": variant.available_stock,
            "price": int(variant.price),
        })
        colors[variant.color_id] = {
            "id": variant.color_id,
            "name": variant.color.name,
            "hex": variant.color.hex_code or "#dddddd",
        }
        sizes[variant.size_id] = {
            "id": variant.size_id,
            "name": variant.size.name,
        }

    mockups = []
    for mockup in product.design_mockups.select_related("color").all():
        mockups.append({
            "side": mockup.side,
            "color_id": mockup.color_id,
            "url": mockup.image.url,
            "print": {
                "x": float(mockup.print_x),
                "y": float(mockup.print_y),
                "width": float(mockup.print_width),
                "height": float(mockup.print_height),
            },
        })

    return {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "price": int(product.base_price),
        "image": image.image.url if image else None,
        "colors": list(colors.values()),
        "sizes": list(sizes.values()),
        "variants": variants,
        "mockups": mockups,
        "studio": {
            "garment_type": getattr(getattr(product, "studio_profile", None), "garment_type", "tee"),
            "default_fabric": getattr(getattr(getattr(product, "studio_profile", None), "default_fabric", None), "slug", None),
            "enabled": getattr(getattr(product, "studio_profile", None), "is_enabled", True),
            "front_reference": getattr(getattr(product, "studio_profile", None), "front_reference", None).url if getattr(getattr(product, "studio_profile", None), "front_reference", None) else (image.image.url if image else None),
            "back_reference": getattr(getattr(product, "studio_profile", None), "back_reference", None).url if getattr(getattr(product, "studio_profile", None), "back_reference", None) else None,
            "left_sleeve_reference": getattr(getattr(product, "studio_profile", None), "left_sleeve_reference", None).url if getattr(getattr(product, "studio_profile", None), "left_sleeve_reference", None) else None,
            "right_sleeve_reference": getattr(getattr(product, "studio_profile", None), "right_sleeve_reference", None).url if getattr(getattr(product, "studio_profile", None), "right_sleeve_reference", None) else None,
            "neck_label_reference": getattr(getattr(product, "studio_profile", None), "neck_label_reference", None).url if getattr(getattr(product, "studio_profile", None), "neck_label_reference", None) else None,
            "print_zones": getattr(getattr(product, "studio_profile", None), "print_zones", {}) or {},
        },
    }


def _public_queryset():
    return (
        Design.objects
        .filter(status=Design.Status.PUBLISHED, visibility=Design.Visibility.PUBLIC)
        .select_related("owner", "base_product", "base_product__studio_profile", "base_color", "parent_design", "parent_design__owner")
        .prefetch_related("base_product__images", "base_product__design_mockups__color", "likes", "saves", "remixes")
    )


def _preview_payload(design):
    data = design.design_data or {}
    sides = data.get("sides", {})
    front = sides.get("front", []) or []
    back = sides.get("back", []) or []
    side = "front" if front or not back else "back"
    layers = front if side == "front" else back
    coordinate_space = data.get("coordinateSpace") or ""
    stage_mode = coordinate_space == "garment-stage-v2"

    mockup = (
        design.base_product.design_mockups
        .filter(side=side, color=design.base_color)
        .first()
        or design.base_product.design_mockups.filter(side=side, color__isnull=True).first()
    )
    fallback = design.base_product.images.first()

    profile = getattr(design.base_product, "studio_profile", None)
    stage_reference = None
    if profile is not None:
        stage_reference = getattr(profile, f"{side}_reference", None)

    if stage_mode and stage_reference:
        image_url = stage_reference.url
        print_box = (profile.print_zones or {}).get(side) or {
            "x": 25, "y": 22, "width": 50, "height": 55,
        }
    elif mockup:
        image_url = mockup.image.url
        print_box = {
            "x": float(mockup.print_x),
            "y": float(mockup.print_y),
            "width": float(mockup.print_width),
            "height": float(mockup.print_height),
        }
    else:
        image_url = fallback.image.url if fallback else None
        print_box = {"x": 25, "y": 22, "width": 50, "height": 55}

    return {
        "side": side,
        "layers": layers,
        "image_url": image_url,
        "print": print_box,
        "coordinate_space": coordinate_space,
        "stage_mode": stage_mode,
    }


def garment_chooser(request):
    products = (
        Product.objects
        .filter(is_active=True, product_type=Product.ProductType.CUSTOMIZABLE)
        .select_related("category", "studio_profile", "studio_profile__default_fabric")
        .prefetch_related("images", "variants__color", "variants__size")
        .order_by("category__sort_order", "name")
    )
    cards = []
    for product in products:
        profile = getattr(product, "studio_profile", None)
        if profile is not None and not profile.is_enabled:
            continue
        if profile and profile.front_reference:
            image_url = profile.front_reference.url
        else:
            primary = product.images.first()
            image_url = primary.image.url if primary else ""
        variants = list(product.variants.filter(is_active=True).select_related("color", "size"))
        colors = {}
        sizes = set()
        in_stock = False
        for variant in variants:
            colors[variant.color_id] = {"name": variant.color.name, "hex": variant.color.hex_code or "#dddddd"}
            sizes.add(variant.size.name)
            if variant.available_stock > 0:
                in_stock = True
        cards.append({
            "product": product,
            "profile": profile,
            "image_url": image_url,
            "colors": list(colors.values()),
            "sizes": sorted(sizes),
            "in_stock": in_stock,
            "has_3d_model": bool(profile and profile.model_file),
        })
    return render(request, "designs/garments.html", {"garment_cards": cards})


def studio(request, design_id=None):
    products_qs = (
        Product.objects
        .filter(is_active=True, product_type=Product.ProductType.CUSTOMIZABLE)
        .select_related("studio_profile", "studio_profile__default_fabric")
        .prefetch_related("images", "variants__color", "variants__size", "design_mockups__color")
        .order_by("name")
    )
    products = [
        product for product in products_qs
        if getattr(getattr(product, "studio_profile", None), "is_enabled", True)
    ]
    studio_settings = StudioSettings.load()
    fabrics = list(FabricOption.objects.filter(is_active=True))
    fonts = list(StudioFont.objects.filter(is_active=True))
    sticker_categories = list(
        StickerCategory.objects.filter(is_active=True).prefetch_related("stickers")
    )

    initial_design = None
    if design_id:
        if not request.user.is_authenticated:
            raise Http404
        design = get_object_or_404(
            Design.objects.select_related("base_product", "base_color"),
            id=design_id, owner=request.user,
        )
        initial_design = {
            "id": str(design.id), "title": design.title, "product_id": design.base_product_id,
            "color_id": design.base_color_id, "status": design.status, "visibility": design.visibility,
            "allow_remix": design.allow_remix, "is_for_sale": design.is_for_sale,
            "sale_price": int(design.sale_price or 0), "design_data": design.design_data,
        }

    requested_product = request.GET.get("product")
    if not initial_design and requested_product:
        try:
            selected = next(product for product in products if str(product.id) == str(requested_product))
            products.remove(selected); products.insert(0, selected)
        except StopIteration:
            pass

    stickers_payload = []
    for category in sticker_categories:
        stickers_payload.append({
            "id": category.id, "name": category.name, "name_fa": category.name_fa, "slug": category.slug,
            "stickers": [
                {"id": sticker.id, "title": sticker.title, "title_fa": sticker.title_fa,
                 "url": sticker.image.url, "preview": sticker.preview_url}
                for sticker in category.stickers.all() if sticker.is_active
            ],
        })

    return render(request, "designs/studio.html", {
        "studio_products": [_product_payload(product) for product in products],
        "initial_design": initial_design,
        "is_authenticated_for_studio": request.user.is_authenticated,
        "creator_pricing_enabled": MarketplaceSettings.load().creator_pricing_enabled,
        "studio_fabrics": [{"id": f.id, "name": f.name, "name_fa": f.name_fa, "slug": f.slug,
                            "roughness": f.roughness, "weave": f.weave_strength, "scale": f.weave_scale, "sheen": f.sheen}
                           for f in fabrics],
        "studio_fonts": [{"id": f.id, "name": f.name, "language": f.language_support, "family": f.css_family,
                           "file_url": f.font_file.url if f.font_file else ""} for f in fonts],
        "sticker_library": stickers_payload,
        "studio_settings": {"ai_enabled": studio_settings.ai_enabled, "ai_configured": ai_is_configured(),
                            "allow_user_stickers": studio_settings.allow_user_stickers,
                            "inspiration_enabled": studio_settings.inspiration_enabled},
        "studio_owner_mode": bool(request.user.is_authenticated and request.user.is_superuser),
    })


@login_required(login_url="/account/login/")
def my_designs(request):
    designs = (
        Design.objects
        .filter(owner=request.user)
        .select_related("base_product", "base_color")
        .annotate(likes_total=Count("likes"), remixes_total=Count("remixes"))
        .order_by("-updated_at")
    )
    return render(request, "designs/my_designs.html", {"designs": designs})


def explore(request):
    sort = request.GET.get("sort", "newest")
    qs = _public_queryset().annotate(
        likes_total=Count("likes", distinct=True),
        remixes_total=Count("remixes", distinct=True),
    )
    if sort == "popular":
        qs = qs.order_by("-likes_total", "-remixes_total", "-published_at")
    else:
        qs = qs.order_by("-published_at")

    cards = [{"design": design, "preview": _preview_payload(design)} for design in qs[:48]]
    return render(request, "designs/explore.html", {"cards": cards, "sort": sort})


def public_design(request, design_id):
    design = get_object_or_404(_public_queryset(), id=design_id)
    preview = _preview_payload(design)
    product = _product_payload(design.base_product)
    color_id = design.base_color_id
    variants = [v for v in product["variants"] if not color_id or v["color_id"] == color_id]
    product["variants"] = variants
    seen_sizes = set()
    filtered_sizes = []
    for variant in variants:
        if variant["size_id"] in seen_sizes:
            continue
        seen_sizes.add(variant["size_id"])
        filtered_sizes.append({"id": variant["size_id"], "name": variant["size"]})
    product["sizes"] = filtered_sizes

    related_qs = (
        _public_queryset()
        .filter(base_product=design.base_product)
        .exclude(id=design.id)
        .order_by("-published_at")[:4]
    )
    related = [{"design": item, "preview": _preview_payload(item)} for item in related_qs]

    liked = False
    saved = False
    if request.user.is_authenticated:
        liked = design.likes.filter(user=request.user).exists()
        saved = design.saves.filter(user=request.user).exists()

    return render(
        request,
        "designs/public_design.html",
        {
            "design": design,
            "preview": preview,
            "purchase_product": product,
            "related": related,
            "liked": liked,
            "saved": saved,
            "creator_pricing_enabled": MarketplaceSettings.load().creator_pricing_enabled,
            "purchase_design_fee": (
                int(design.sale_price or 0)
                if MarketplaceSettings.load().creator_pricing_enabled
                and not (request.user.is_authenticated and request.user.id == design.owner_id)
                else 0
            ),
        },
    )


# ---- Stage 4: creator profiles, following and saved designs ----
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.accounts.models import CreatorFollow
from apps.notifications.models import Notification
from .models import DesignSave

User = get_user_model()


def creator_profile(request, username):
    creator = get_object_or_404(User, username__iexact=username)
    if not creator.public_profile_enabled and request.user != creator:
        raise Http404

    qs = (
        _public_queryset()
        .filter(owner=creator)
        .annotate(
            likes_total=Count("likes", distinct=True),
            remixes_total=Count("remixes", distinct=True),
        )
        .order_by("-published_at")
    )

    cards = [
        {"design": design, "preview": _preview_payload(design)}
        for design in qs[:48]
    ]

    is_following = False
    if request.user.is_authenticated and request.user != creator:
        is_following = CreatorFollow.objects.filter(
            follower=request.user,
            creator=creator,
        ).exists()

    return render(
        request,
        "designs/creator_profile.html",
        {
            "creator": creator,
            "cards": cards,
            "is_following": is_following,
            "followers_count": creator.creator_followers.count(),
            "following_count": creator.following_creators.count(),
        },
    )


@login_required(login_url="/account/login/")
@require_POST
def creator_follow_toggle(request, username):
    creator = get_object_or_404(
        User,
        username__iexact=username,
        public_profile_enabled=True,
    )

    if creator.id == request.user.id:
        return JsonResponse({"detail": "You cannot follow yourself."}, status=400)

    follow, created = CreatorFollow.objects.get_or_create(
        follower=request.user,
        creator=creator,
    )

    if not created:
        follow.delete()
    else:
        Notification.objects.create(
            user=creator,
            kind=Notification.Kind.SOCIAL,
            title="New follower",
            body=f"{request.user.display_name or request.user.username} started following you.",
            url=(f"/creator/{request.user.username}/" if request.user.public_profile_enabled else "/account/notifications/"),
        )

    return JsonResponse(
        {
            "active": created,
            "followers": creator.creator_followers.count(),
        }
    )


@login_required(login_url="/account/login/")
def saved_designs(request):
    saves = (
        DesignSave.objects.filter(user=request.user)
        .select_related(
            "design",
            "design__owner",
            "design__base_product",
            "design__base_color",
        )
        .prefetch_related(
            "design__base_product__images",
            "design__base_product__design_mockups__color",
        )
        .order_by("-created_at")
    )

    cards = []
    for saved in saves:
        design = saved.design
        if (
            design.status != Design.Status.PUBLISHED
            or design.visibility != Design.Visibility.PUBLIC
        ):
            continue
        cards.append(
            {
                "design": design,
                "preview": _preview_payload(design),
                "saved_at": saved.created_at,
            }
        )

    return render(
        request,
        "designs/saved_designs.html",
        {"cards": cards},
    )
