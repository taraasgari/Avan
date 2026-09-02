from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render

from apps.accounts.models import CreatorFollow
from apps.orders.models import Order, OrderItem
from apps.marketplace.models import CreatorWallet

from .models import Design
from .web_views import _preview_payload, _public_queryset


@login_required(login_url="/account/login/")
def following_feed(request):
    creator_ids = CreatorFollow.objects.filter(
        follower=request.user
    ).values_list("creator_id", flat=True)

    qs = (
        _public_queryset()
        .filter(owner_id__in=creator_ids)
        .annotate(
            likes_total=Count("likes", distinct=True),
            remixes_total=Count("remixes", distinct=True),
        )
        .order_by("-published_at")[:60]
    )

    cards = [
        {"design": design, "preview": _preview_payload(design)}
        for design in qs
    ]

    return render(
        request,
        "designs/following.html",
        {"cards": cards},
    )


@login_required(login_url="/account/login/")
def creator_analytics(request):
    designs = (
        Design.objects.filter(owner=request.user)
        .annotate(
            likes_total=Count("likes", distinct=True),
            saves_total=Count("saves", distinct=True),
            remixes_total=Count("remixes", distinct=True),
        )
        .order_by("-updated_at")
    )

    public_designs = designs.filter(
        status=Design.Status.PUBLISHED,
        visibility=Design.Visibility.PUBLIC,
    )
    design_ids = list(designs.values_list("id", flat=True))

    paid_statuses = [
        Order.Status.PAID,
        Order.Status.PROCESSING,
        Order.Status.SHIPPED,
        Order.Status.DELIVERED,
    ]

    wear_qs = OrderItem.objects.filter(
        design_id_snapshot__in=design_ids,
        order__status__in=paid_statuses,
    )

    wear_totals = wear_qs.aggregate(
        pieces=Sum("quantity"),
    )

    rows = []
    for design in public_designs[:24]:
        design_wears = wear_qs.filter(design_id_snapshot=design.id).aggregate(
            pieces=Sum("quantity")
        )["pieces"] or 0
        rows.append(
            {
                "design": design,
                "preview": _preview_payload(design),
                "wears": design_wears,
            }
        )

    wallet, _ = CreatorWallet.objects.get_or_create(creator=request.user)
    totals = {
        "published": public_designs.count(),
        "followers": request.user.creator_followers.count(),
        "likes": sum(item.likes_total for item in public_designs),
        "saves": sum(item.saves_total for item in public_designs),
        "remixes": sum(item.remixes_total for item in public_designs),
        "wears": wear_totals["pieces"] or 0,
        "orders": wear_qs.values("order_id").distinct().count(),
        "earned": wallet.total_earned,
        "available": wallet.available_balance,
        "pending": wallet.pending_payout,
    }

    return render(
        request,
        "designs/creator_analytics.html",
        {"totals": totals, "rows": rows, "creator_wallet": wallet},
    )
