from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.models import CreatorFollow
from apps.catalog.models import Product
from apps.designs.models import Design
from apps.designs.web_views import _preview_payload, _public_queryset
from apps.orders.models import Order
from apps.wishlist.models import WishlistItem

from .models import CreatorWallet, MarketplaceSettings, PayoutRequest
from .services import create_payout_request, redeem_points_for_coupon


@login_required(login_url="/account/login/")
def creator_wallet(request):
    wallet, _ = CreatorWallet.objects.get_or_create(creator=request.user)
    earnings = request.user.creator_earnings.select_related("order_item", "design")[:60]
    payouts = request.user.payout_requests.all()[:30]
    config = MarketplaceSettings.load()
    return render(
        request,
        "marketplace/creator_wallet.html",
        {"wallet": wallet, "earnings": earnings, "payouts": payouts, "marketplace_config": config},
    )


@login_required(login_url="/account/login/")
@require_POST
def request_payout(request):
    try:
        create_payout_request(
            creator=request.user,
            amount=request.POST.get("amount", "0"),
            note=request.POST.get("note", ""),
        )
    except (ValueError, TypeError) as exc:
        wallet, _ = CreatorWallet.objects.get_or_create(creator=request.user)
        config = MarketplaceSettings.load()
        return render(
            request,
            "marketplace/creator_wallet.html",
            {
                "wallet": wallet,
                "earnings": request.user.creator_earnings.select_related("order_item", "design")[:60],
                "payouts": request.user.payout_requests.all()[:30],
                "marketplace_config": config,
                "payout_error": str(exc),
            },
            status=400,
        )
    return redirect("marketplace:creator-wallet")


@login_required(login_url="/account/login/")
@require_POST
def redeem_points(request):
    try:
        coupon = redeem_points_for_coupon(user=request.user)
    except ValueError as exc:
        return redirect(f"/rewards/?redeem_error={str(exc)}")
    return redirect(f"/rewards/?coupon={coupon.code}")


@login_required(login_url="/account/login/")
def for_you(request):
    followed_ids = list(
        CreatorFollow.objects.filter(follower=request.user).values_list("creator_id", flat=True)
    )
    saved_product_ids = list(
        request.user.saved_designs.values_list("design__base_product_id", flat=True)
    )
    wishlist_category_ids = list(
        WishlistItem.objects.filter(user=request.user).values_list("product__category_id", flat=True)
    )
    bought_category_ids = list(
        Product.objects.filter(
            variants__order_items__order__user=request.user,
            variants__order_items__order__status__in=[
                Order.Status.PAID, Order.Status.PROCESSING, Order.Status.SHIPPED, Order.Status.DELIVERED,
            ],
        ).values_list("category_id", flat=True)
    )

    pool = (
        _public_queryset()
        .annotate(likes_total=Count("likes", distinct=True), remixes_total=Count("remixes", distinct=True))
        .filter(
            Q(owner_id__in=followed_ids)
            | Q(base_product_id__in=saved_product_ids)
            | Q(base_product__category_id__in=set(wishlist_category_ids + bought_category_ids))
        )
        .order_by("-likes_total", "-published_at")
    )

    seen = set()
    designs = []
    for design in pool[:60]:
        if design.id not in seen:
            seen.add(design.id)
            designs.append({"design": design, "preview": _preview_payload(design)})
        if len(designs) >= 24:
            break

    if len(designs) < 24:
        fallback = _public_queryset().annotate(likes_total=Count("likes", distinct=True)).order_by("-likes_total", "-published_at")
        for design in fallback[:60]:
            if design.id in seen:
                continue
            seen.add(design.id)
            designs.append({"design": design, "preview": _preview_payload(design)})
            if len(designs) >= 24:
                break

    product_categories = set(wishlist_category_ids + bought_category_ids)
    products = Product.objects.filter(is_active=True)
    if product_categories:
        products = products.filter(category_id__in=product_categories)
    products = products.prefetch_related("images").order_by("-is_featured", "-created_at")[:12]

    return render(request, "marketplace/for_you.html", {"cards": designs, "products": products})
