import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core import signing
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.coupons.models import Coupon
from apps.designs.models import Design
from apps.designs.web_views import _preview_payload
from .models import Challenge, ChallengeEntry, Drop, GameScore, RewardWallet, SoloGame
from .services import grant_points


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
            cards.append({"kind": "product", "item": item, "image_url": image.image.url if image else None})
        elif item.design_id:
            design = item.design
            if design.status == Design.Status.PUBLISHED and design.visibility == Design.Visibility.PUBLIC:
                cards.append({"kind": "design", "item": item, "preview": _preview_payload(design)})

    return render(request, "experience/drop_detail.html", {"drop": drop, "cards": cards})


@login_required(login_url="/account/login/")
def challenges(request):
    challenge_list = (
        Challenge.objects.filter(
            is_enabled=True,
            status__in=[Challenge.Status.PUBLISHED, Challenge.Status.CLOSED],
        )
        .select_related("garment_product")
        .annotate(entry_count=Count("entries", distinct=True))
        .order_by("-starts_at", "-created_at")
    )
    return render(request, "experience/challenges.html", {"challenges": challenge_list})


@login_required(login_url="/account/login/")
def challenge_detail(request, slug):
    challenge = get_object_or_404(
        Challenge.objects.filter(
            is_enabled=True,
            status__in=[Challenge.Status.PUBLISHED, Challenge.Status.CLOSED],
        ).select_related("garment_product"),
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
            if challenge.garment_product_id and design.base_product_id != challenge.garment_product_id:
                error = "This design uses a different garment than the challenge requires."
            else:
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
        my_designs_qs = Design.objects.filter(
            owner=request.user,
            status=Design.Status.PUBLISHED,
            visibility=Design.Visibility.PUBLIC,
        )
        if challenge.garment_product_id:
            my_designs_qs = my_designs_qs.filter(base_product_id=challenge.garment_product_id)
        my_designs = list(my_designs_qs.order_by("-published_at"))

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
def play_hub(request):
    games = list(SoloGame.objects.filter(is_enabled=True).order_by("sort_order", "id"))
    week_start = timezone.now() - timedelta(days=7)
    leaderboard = (
        GameScore.objects.filter(played_at__gte=week_start, game__is_enabled=True)
        .select_related("user", "game")
        .order_by("-score", "played_at")[:12]
    )
    my_best = {}
    if request.user.is_authenticated:
        for row in GameScore.objects.filter(user=request.user, game__is_enabled=True).order_by("game_id", "-score"):
            my_best.setdefault(row.game_id, row.score)
    for game in games:
        game.user_best = my_best.get(game.id)
    return render(
        request,
        "experience/play.html",
        {"games": games, "leaderboard": leaderboard},
    )


@login_required(login_url="/account/login/")
def game_detail(request, slug):
    game = get_object_or_404(SoloGame, slug=slug, is_enabled=True)
    best_score = None
    if request.user.is_authenticated:
        best = GameScore.objects.filter(game=game, user=request.user).order_by("-score").first()
        best_score = best.score if best else None
    return render(request, "experience/game.html", {"game": game, "best_score": best_score})


@login_required(login_url="/account/login/")
@require_POST
def game_start(request, slug):
    game = get_object_or_404(SoloGame, slug=slug, is_enabled=True)
    payload = {
        "game_id": game.id,
        "user_id": request.user.id,
        "started_at": int(timezone.now().timestamp()),
    }
    token = signing.dumps(payload, salt="avan-play-run")
    return JsonResponse({"ok": True, "token": token})


@login_required(login_url="/account/login/")
@require_POST
def game_submit(request, slug):
    game = get_object_or_404(SoloGame, slug=slug, is_enabled=True)
    try:
        data = json.loads(request.body.decode("utf-8"))
        score = int(data.get("score", 0))
        token = str(data.get("token", ""))
        payload = signing.loads(token, salt="avan-play-run", max_age=600)
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid_run"}, status=400)

    expected_user_id = request.user.id
    if payload.get("game_id") != game.id or payload.get("user_id") != expected_user_id:
        return JsonResponse({"ok": False, "error": "run_mismatch"}, status=400)

    now_ts = int(timezone.now().timestamp())
    elapsed = max(1, now_ts - int(payload.get("started_at", now_ts)))
    if elapsed < 3 or elapsed > 600:
        return JsonResponse({"ok": False, "error": "invalid_duration"}, status=400)

    plausible_max = min(game.score_cap, elapsed * game.max_score_per_second + 400)
    if score < 0 or score > plausible_max:
        return JsonResponse({"ok": False, "error": "score_rejected"}, status=400)

    reward = game.reward_bundle_for(score)
    tier = reward["tier"]
    points_awarded = 0
    reward_unlocked = False
    today = timezone.localdate().isoformat()

    if reward["points"] > 0:
        _, granted = grant_points(
            user=request.user,
            amount=reward["points"],
            reason=f"{game.title} — {tier.upper()} run",
            reference=f"solo-game:{game.id}:{request.user.id}:{today}:{tier}:points",
        )
        points_awarded = reward["points"] if granted else 0
        reward_unlocked = reward_unlocked or granted

    expires_at = timezone.now() + timedelta(days=max(1, game.reward_expiry_days))
    if reward["discount_percent"] > 0:
        code = f"PLAY-{game.id}-{request.user.id}-{timezone.localdate():%y%m%d}-{tier[:1].upper()}D"
        _, created = Coupon.objects.get_or_create(
            code=code,
            defaults={
                "discount_type": Coupon.DiscountType.PERCENT,
                "value": min(Decimal("100"), Decimal(reward["discount_percent"])),
                "assigned_user": request.user,
                "usage_limit": 1,
                "usage_limit_per_user": 1,
                "ends_at": expires_at,
                "is_active": True,
            },
        )
        reward_unlocked = reward_unlocked or created

    if reward["subsidy_amount"] > 0:
        code = f"PLAY-{game.id}-{request.user.id}-{timezone.localdate():%y%m%d}-{tier[:1].upper()}C"
        _, created = Coupon.objects.get_or_create(
            code=code,
            defaults={
                "discount_type": Coupon.DiscountType.FIXED,
                "value": reward["subsidy_amount"],
                "assigned_user": request.user,
                "usage_limit": 1,
                "usage_limit_per_user": 1,
                "ends_at": expires_at,
                "is_active": True,
            },
        )
        reward_unlocked = reward_unlocked or created

    GameScore.objects.create(
        game=game,
        user=request.user,
        score=score,
        reward_tier=tier,
        points_awarded=points_awarded,
    )

    return JsonResponse(
        {
            "ok": True,
            "score": score,
            "tier": tier,
            "saved": True,
            "authenticated": True,
            "reward_unlocked": reward_unlocked,
        }
    )


@login_required(login_url="/account/login/")
def rewards(request):
    wallet, _ = RewardWallet.objects.get_or_create(user=request.user)
    transactions = wallet.transactions.all()[:100]
    play_coupons = (
        Coupon.objects.filter(assigned_user=request.user, is_active=True)
        .filter(Q(code__startswith="PLAY-") | Q(code__startswith="CHAL-"))
        .order_by("-created_at")[:30]
    )
    return render(
        request,
        "experience/rewards.html",
        {"wallet": wallet, "transactions": transactions, "play_coupons": play_coupons},
    )
