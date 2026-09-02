from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.designs.models import Design
from apps.designs.web_views import _preview_payload
from .models import Challenge, ChallengeEntry, Drop, RewardWallet


def drops(request):
    drop_list = (
        Drop.objects.filter(status=Drop.Status.PUBLISHED)
        .prefetch_related(
            "items__product__images",
            "items__design__owner",
            "items__design__base_product__images",
            "items__design__base_product__design_mockups__color",
        )
        .order_by("-is_featured", "-starts_at", "-created_at")
    )
    return render(request, "experience/drops.html", {"drops": drop_list})


def drop_detail(request, slug):
    drop = get_object_or_404(
        Drop.objects.filter(status=Drop.Status.PUBLISHED).prefetch_related(
            "items__product__images",
            "items__design__owner",
            "items__design__base_product__images",
            "items__design__base_product__design_mockups__color",
        ),
        slug=slug,
    )

    cards = []
    for item in drop.items.all():
        if item.product_id:
            image = item.product.images.first()
            cards.append(
                {
                    "kind": "product",
                    "item": item,
                    "image_url": image.image.url if image else None,
                }
            )
        elif item.design_id:
            design = item.design
            if (
                design.status == Design.Status.PUBLISHED
                and design.visibility == Design.Visibility.PUBLIC
            ):
                cards.append(
                    {
                        "kind": "design",
                        "item": item,
                        "preview": _preview_payload(design),
                    }
                )

    return render(
        request,
        "experience/drop_detail.html",
        {"drop": drop, "cards": cards},
    )


def challenges(request):
    challenge_list = (
        Challenge.objects.filter(status__in=[Challenge.Status.PUBLISHED, Challenge.Status.CLOSED])
        .annotate(entry_count=Count("entries", distinct=True))
        .order_by("-starts_at", "-created_at")
    )
    return render(request, "experience/challenges.html", {"challenges": challenge_list})


def challenge_detail(request, slug):
    challenge = get_object_or_404(
        Challenge.objects.filter(status__in=[Challenge.Status.PUBLISHED, Challenge.Status.CLOSED]),
        slug=slug,
    )

    error = None
    success = None

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(f"/account/login/?next=/challenges/{challenge.slug}/")

        if not challenge.is_open:
            error = "This challenge is not accepting entries right now."
        else:
            design_id = request.POST.get("design_id")
            design = get_object_or_404(
                Design,
                id=design_id,
                owner=request.user,
                status=Design.Status.PUBLISHED,
                visibility=Design.Visibility.PUBLIC,
            )
            _, created = ChallengeEntry.objects.get_or_create(
                challenge=challenge,
                user=request.user,
                design=design,
                defaults={"note": request.POST.get("note", "")[:240]},
            )
            if created:
                success = "Design submitted to the challenge."
            else:
                error = "This design is already entered in this challenge."

    my_designs = []
    if request.user.is_authenticated:
        my_designs = list(
            Design.objects.filter(
                owner=request.user,
                status=Design.Status.PUBLISHED,
                visibility=Design.Visibility.PUBLIC,
            ).order_by("-published_at")
        )

    entries = (
        challenge.entries.select_related("user", "design", "design__base_product")
        .filter(status__in=[ChallengeEntry.Status.FINALIST, ChallengeEntry.Status.WINNER])
        .order_by("-status", "-created_at")
    )

    return render(
        request,
        "experience/challenge_detail.html",
        {
            "challenge": challenge,
            "my_designs": my_designs,
            "entries": entries,
            "error": error,
            "success": success,
        },
    )


@login_required(login_url="/account/login/")
def rewards(request):
    wallet, _ = RewardWallet.objects.get_or_create(user=request.user)
    transactions = wallet.transactions.all()[:100]
    return render(
        request,
        "experience/rewards.html",
        {"wallet": wallet, "transactions": transactions},
    )
