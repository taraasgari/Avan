from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import render

from apps.catalog.models import Product
from apps.designs.models import Design
from apps.designs.web_views import _preview_payload


User = get_user_model()


def search(request):
    query = (request.GET.get("q") or "").strip()[:80]

    products = Product.objects.none()
    designs = Design.objects.none()
    creators = User.objects.none()

    design_cards = []

    if len(query) >= 2:
        products = (
            Product.objects.filter(is_active=True)
            .filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(category__name__icontains=query)
            )
            .select_related("category")
            .prefetch_related("images")
            .distinct()[:24]
        )

        designs = (
            Design.objects.filter(
                status=Design.Status.PUBLISHED,
                visibility=Design.Visibility.PUBLIC,
            )
            .filter(
                Q(title__icontains=query)
                | Q(owner__username__icontains=query)
                | Q(owner__display_name__icontains=query)
                | Q(base_product__name__icontains=query)
            )
            .select_related("owner", "base_product", "base_color")
            .prefetch_related(
                "base_product__images",
                "base_product__design_mockups__color",
            )
            .annotate(likes_total=Count("likes", distinct=True))
            .distinct()[:24]
        )
        design_cards = [
            {"design": design, "preview": _preview_payload(design)}
            for design in designs
        ]

        creators = (
            User.objects.filter(public_profile_enabled=True)
            .filter(
                Q(username__icontains=query)
                | Q(display_name__icontains=query)
                | Q(bio__icontains=query)
            )
            .annotate(followers_total=Count("creator_followers", distinct=True))
            .order_by("-followers_total", "username")[:16]
        )

    return render(
        request,
        "core/search.html",
        {
            "query": query,
            "products": products,
            "design_cards": design_cards,
            "creators": creators,
        },
    )
