from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from apps.catalog.models import Product
from apps.marketplace.models import MarketplaceSettings
from .models import Design


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
    }


def _public_queryset():
    return (
        Design.objects
        .filter(status=Design.Status.PUBLISHED, visibility=Design.Visibility.PUBLIC)
        .select_related("owner", "base_product", "base_color", "parent_design", "parent_design__owner")
        .prefetch_related("base_product__images", "base_product__design_mockups__color", "likes", "saves", "remixes")
    )


def _preview_payload(design):
    sides = (design.design_data or {}).get("sides", {})
    front = sides.get("front", []) or []
    back = sides.get("back", []) or []
    side = "front" if front or not back else "back"
    layers = front if side == "front" else back

    mockup = (
        design.base_product.design_mockups
        .filter(side=side, color=design.base_color)
        .first()
        or design.base_product.design_mockups.filter(side=side, color__isnull=True).first()
    )
    fallback = design.base_product.images.first()

    if mockup:
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
    }


def studio(request, design_id=None):
    products_qs = (
        Product.objects
        .filter(is_active=True, product_type=Product.ProductType.CUSTOMIZABLE)
        .prefetch_related(
            "images", "variants__color", "variants__size", "design_mockups__color"
        )
        .order_by("name")
    )
    products = list(products_qs)
    if not products:
        return render(request, "designs/studio.html", {"studio_products": [], "initial_design": None, "creator_pricing_enabled": MarketplaceSettings.load().creator_pricing_enabled})

    initial_design = None
    if design_id:
        if not request.user.is_authenticated:
            raise Http404
        design = get_object_or_404(
            Design.objects.select_related("base_product", "base_color"),
            id=design_id,
            owner=request.user,
        )
        initial_design = {
            "id": str(design.id),
            "title": design.title,
            "product_id": design.base_product_id,
            "color_id": design.base_color_id,
            "status": design.status,
            "visibility": design.visibility,
            "allow_remix": design.allow_remix,
            "is_for_sale": design.is_for_sale,
            "sale_price": int(design.sale_price or 0),
            "design_data": design.design_data,
        }

    requested_product = request.GET.get("product")
    if not initial_design and requested_product:
        try:
            selected = next(product for product in products if str(product.id) == str(requested_product))
            products.remove(selected)
            products.insert(0, selected)
        except StopIteration:
            pass

    return render(
        request,
        "designs/studio.html",
        {
            "studio_products": [_product_payload(product) for product in products],
            "initial_design": initial_design,
            "is_authenticated_for_studio": request.user.is_authenticated,
            "creator_pricing_enabled": MarketplaceSettings.load().creator_pricing_enabled,
        },
    )


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
