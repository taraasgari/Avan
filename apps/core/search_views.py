from django.contrib.auth import get_user_model
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.http import JsonResponse
from django.shortcuts import render

from apps.catalog.models import Category, Product
from apps.contentstudio.models import Collection
from apps.designs.models import Design
from apps.designs.web_views import _preview_payload


User = get_user_model()


def _lang(request):
    return "fa" if str(getattr(request, "avan_language", "fa")).startswith("fa") else "en"


def _product_search(query, limit=24):
    return (
        Product.objects.filter(is_active=True)
        .filter(
            Q(search_tags__icontains=query)
            | Q(name__icontains=query)
            | Q(name_fa__icontains=query)
            | Q(name_en__icontains=query)
            | Q(description__icontains=query)
            | Q(description_fa__icontains=query)
            | Q(description_en__icontains=query)
            | Q(category__name__icontains=query)
            | Q(category__name_fa__icontains=query)
            | Q(category__name_en__icontains=query)
        )
        .annotate(
            tag_rank=Case(
                When(search_tags__icontains=query, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .select_related("category")
        .prefetch_related("images")
        .order_by("tag_rank", "-is_featured", "name")
        .distinct()[:limit]
    )


def search(request):
    query = (request.GET.get("q") or "").strip()[:80]
    products = Product.objects.none()
    designs = Design.objects.none()
    creators = User.objects.none()
    categories = Category.objects.none()
    collections = Collection.objects.none()
    design_cards = []

    if len(query) >= 2:
        products = _product_search(query, 24)
        categories = (
            Category.objects.filter(is_active=True)
            .filter(Q(name__icontains=query) | Q(name_fa__icontains=query) | Q(name_en__icontains=query))
            .order_by("sort_order", "name")[:12]
        )
        collections = (
            Collection.objects.filter(is_active=True)
            .filter(
                Q(name_fa__icontains=query)
                | Q(name_en__icontains=query)
                | Q(description_fa__icontains=query)
                | Q(description_en__icontains=query)
                | Q(products__search_tags__icontains=query)
            )
            .select_related("hero")
            .distinct()[:12]
        )
        designs = (
            Design.objects.filter(status=Design.Status.PUBLISHED, visibility=Design.Visibility.PUBLIC)
            .filter(
                Q(title__icontains=query)
                | Q(owner__username__icontains=query)
                | Q(owner__display_name__icontains=query)
                | Q(base_product__name__icontains=query)
                | Q(base_product__search_tags__icontains=query)
            )
            .select_related("owner", "base_product", "base_color")
            .prefetch_related("base_product__images", "base_product__design_mockups__color")
            .annotate(likes_total=Count("likes", distinct=True))
            .distinct()[:24]
        )
        design_cards = [{"design": design, "preview": _preview_payload(design)} for design in designs]
        creators = (
            User.objects.filter(public_profile_enabled=True)
            .filter(Q(username__icontains=query) | Q(display_name__icontains=query) | Q(bio__icontains=query))
            .annotate(followers_total=Count("creator_followers", distinct=True))
            .order_by("-followers_total", "username")[:16]
        )

    return render(
        request,
        "core/search.html",
        {
            "query": query,
            "products": products,
            "categories": categories,
            "collections": collections,
            "design_cards": design_cards,
            "creators": creators,
        },
    )


def search_suggest(request):
    query = (request.GET.get("q") or "").strip()[:80]
    if len(query) < 2:
        return JsonResponse({"query": query, "groups": []})

    language = _lang(request)
    groups = []

    product_items = []
    for product in _product_search(query, 7):
        image = product.images.first()
        product_items.append(
            {
                "title": product.localized_name(language),
                "subtitle": product.category.localized_name(language),
                "url": f"/shop/{product.slug}/",
                "image": image.image.url if image else "",
                "kind": "product",
            }
        )
    if product_items:
        groups.append({"key": "products", "title": "محصولات" if language == "fa" else "Products", "items": product_items})

    category_items = [
        {
            "title": category.localized_name(language),
            "subtitle": "دسته‌بندی" if language == "fa" else "Category",
            "url": f"/shop/?category={category.slug}",
            "image": "",
            "kind": "category",
        }
        for category in Category.objects.filter(is_active=True)
        .filter(Q(name__icontains=query) | Q(name_fa__icontains=query) | Q(name_en__icontains=query))
        .order_by("sort_order", "name")[:5]
    ]
    if category_items:
        groups.append({"key": "categories", "title": "دسته‌بندی‌ها" if language == "fa" else "Categories", "items": category_items})

    collection_items = []
    for collection in (
        Collection.objects.filter(is_active=True)
        .filter(Q(name_fa__icontains=query) | Q(name_en__icontains=query) | Q(products__search_tags__icontains=query))
        .select_related("hero")
        .distinct()[:5]
    ):
        collection_items.append(
            {
                "title": collection.localized_name(language),
                "subtitle": "کالکشن" if language == "fa" else "Collection",
                "url": f"/collections/{collection.slug}/",
                "image": collection.hero.file.url if collection.hero else "",
                "kind": "collection",
            }
        )
    if collection_items:
        groups.append({"key": "collections", "title": "کالکشن‌ها" if language == "fa" else "Collections", "items": collection_items})

    design_items = []
    for design in (
        Design.objects.filter(status=Design.Status.PUBLISHED, visibility=Design.Visibility.PUBLIC)
        .filter(Q(title__icontains=query) | Q(base_product__search_tags__icontains=query))
        .select_related("owner")[:5]
    ):
        design_items.append(
            {
                "title": design.title,
                "subtitle": f"@{design.owner.username}",
                "url": f"/explore/{design.id}/",
                "image": "",
                "kind": "design",
            }
        )
    if design_items:
        groups.append({"key": "designs", "title": "طرح‌ها" if language == "fa" else "Designs", "items": design_items})

    creator_items = [
        {
            "title": creator.display_name or creator.username,
            "subtitle": f"@{creator.username}",
            "url": f"/creator/{creator.username}/",
            "image": creator.avatar.url if creator.avatar else "",
            "kind": "creator",
        }
        for creator in User.objects.filter(public_profile_enabled=True)
        .filter(Q(username__icontains=query) | Q(display_name__icontains=query))[:5]
    ]
    if creator_items:
        groups.append({"key": "creators", "title": "طراحان" if language == "fa" else "Creators", "items": creator_items})

    return JsonResponse({"query": query, "groups": groups})
