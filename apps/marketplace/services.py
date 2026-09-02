import secrets
from decimal import Decimal, ROUND_DOWN

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.coupons.models import Coupon
from apps.experience.models import RewardTransaction, RewardWallet
from apps.notifications.models import Notification

from .models import CreatorEarning, CreatorWallet, MarketplaceSettings, PayoutRequest


User = get_user_model()
MONEY = Decimal("1")


def _money(value):
    return Decimal(value or 0).quantize(MONEY, rounding=ROUND_DOWN)


def split_design_fee(design_fee):
    config = MarketplaceSettings.load()
    if not config.creator_pricing_enabled:
        return Decimal("0"), Decimal("0"), Decimal("0")
    fee = _money(design_fee)
    rate = Decimal(config.commission_percent or 0)
    commission = (fee * rate / Decimal("100")).quantize(MONEY, rounding=ROUND_DOWN)
    creator_amount = max(Decimal("0"), fee - commission)
    return commission, creator_amount, rate


@transaction.atomic
def record_creator_earnings(order):
    created_entries = []
    items = order.items.filter(
        design_fee__gt=0,
        creator_id_snapshot__isnull=False,
    ).select_related("variant")

    for item in items:
        creator = User.objects.filter(pk=item.creator_id_snapshot).first()
        if not creator:
            continue

        earning, created = CreatorEarning.objects.get_or_create(
            order_item=item,
            defaults={
                "creator": creator,
                "design_id_snapshot": item.design_id_snapshot,
                "gross_design_fee": _money(item.design_fee * item.quantity),
                "platform_commission": _money(item.platform_commission_amount * item.quantity),
                "creator_amount": _money(item.creator_earning_amount * item.quantity),
            },
        )
        if not created:
            continue

        # Preserve the optional live relation while snapshots remain authoritative.
        if item.design_id_snapshot:
            from apps.designs.models import Design
            earning.design = Design.objects.filter(pk=item.design_id_snapshot).first()
            if earning.design_id:
                earning.save(update_fields=["design"])

        wallet, _ = CreatorWallet.objects.select_for_update().get_or_create(creator=creator)
        wallet.available_balance += earning.creator_amount
        wallet.total_earned += earning.creator_amount
        wallet.save(update_fields=["available_balance", "total_earned", "updated_at"])

        Notification.objects.create(
            user=creator,
            kind=Notification.Kind.REWARD,
            title="New creator earning",
            body=f"{earning.creator_amount:,.0f} Toman was added from a paid design order.",
            url="/account/creator/wallet/",
        )
        created_entries.append(earning)

    return created_entries


@transaction.atomic
def create_payout_request(*, creator, amount, note=""):
    amount = _money(amount)
    if amount <= 0:
        raise ValueError("Payout amount must be greater than zero.")

    config = MarketplaceSettings.load()
    if config.minimum_payout_amount and amount < config.minimum_payout_amount:
        raise ValueError(f"Minimum payout is {config.minimum_payout_amount:,.0f} Toman.")

    wallet, _ = CreatorWallet.objects.select_for_update().get_or_create(creator=creator)
    if amount > wallet.available_balance:
        raise ValueError("Requested amount is higher than your available balance.")

    wallet.available_balance -= amount
    wallet.pending_payout += amount
    wallet.save(update_fields=["available_balance", "pending_payout", "updated_at"])

    return PayoutRequest.objects.create(
        creator=creator,
        amount=amount,
        creator_note=(note or "")[:240],
    )


@transaction.atomic
def approve_payout(payout):
    payout = PayoutRequest.objects.select_for_update().get(pk=payout.pk)
    if payout.status != PayoutRequest.Status.PENDING:
        return payout, False
    payout.status = PayoutRequest.Status.APPROVED
    payout.reviewed_at = timezone.now()
    payout.save(update_fields=["status", "reviewed_at"])
    return payout, True


@transaction.atomic
def reject_payout(payout, *, admin_note=""):
    payout = PayoutRequest.objects.select_for_update().get(pk=payout.pk)
    if payout.status not in {PayoutRequest.Status.PENDING, PayoutRequest.Status.APPROVED}:
        return payout, False

    wallet = CreatorWallet.objects.select_for_update().get(creator=payout.creator)
    wallet.pending_payout = max(Decimal("0"), wallet.pending_payout - payout.amount)
    wallet.available_balance += payout.amount
    wallet.save(update_fields=["pending_payout", "available_balance", "updated_at"])

    payout.status = PayoutRequest.Status.REJECTED
    payout.admin_note = (admin_note or payout.admin_note)[:240]
    payout.reviewed_at = timezone.now()
    payout.save(update_fields=["status", "admin_note", "reviewed_at"])
    return payout, True


@transaction.atomic
def mark_payout_paid(payout, *, admin_note=""):
    payout = PayoutRequest.objects.select_for_update().get(pk=payout.pk)
    if payout.status != PayoutRequest.Status.APPROVED:
        return payout, False

    wallet = CreatorWallet.objects.select_for_update().get(creator=payout.creator)
    if wallet.pending_payout < payout.amount:
        raise ValueError("Wallet pending balance is inconsistent with this payout.")

    wallet.pending_payout -= payout.amount
    wallet.total_paid += payout.amount
    wallet.save(update_fields=["pending_payout", "total_paid", "updated_at"])

    payout.status = PayoutRequest.Status.PAID
    payout.admin_note = (admin_note or payout.admin_note)[:240]
    payout.paid_at = timezone.now()
    payout.reviewed_at = payout.reviewed_at or timezone.now()
    payout.save(update_fields=["status", "admin_note", "paid_at", "reviewed_at"])

    Notification.objects.create(
        user=payout.creator,
        kind=Notification.Kind.REWARD,
        title="Creator payout marked paid",
        body=f"Your payout of {payout.amount:,.0f} Toman was marked as paid by AVAN.",
        url="/account/creator/wallet/",
    )
    return payout, True


@transaction.atomic
def redeem_points_for_coupon(*, user):
    config = MarketplaceSettings.load()
    cost = int(config.points_redemption_cost or 0)
    value = _money(config.points_coupon_value)
    if cost <= 0 or value <= 0:
        raise ValueError("Points redemption is not enabled yet.")

    wallet, _ = RewardWallet.objects.select_for_update().get_or_create(user=user)
    if wallet.balance < cost:
        raise ValueError("You do not have enough AVAN Points.")

    code = f"PTS-{user.pk}-{secrets.token_hex(4).upper()}"
    coupon = Coupon.objects.create(
        code=code,
        discount_type=Coupon.DiscountType.FIXED,
        value=value,
        minimum_subtotal=config.points_coupon_minimum_subtotal,
        usage_limit=1,
        usage_limit_per_user=1,
        assigned_user=user,
        is_active=True,
    )

    RewardTransaction.objects.create(
        wallet=wallet,
        amount=-cost,
        reason=f"Redeemed for {value:,.0f} Toman coupon",
        reference=f"points-coupon:{coupon.pk}",
    )
    wallet.balance -= cost
    wallet.save(update_fields=["balance", "updated_at"])

    Notification.objects.create(
        user=user,
        kind=Notification.Kind.REWARD,
        title="Reward coupon created",
        body=f"{cost} AVAN Points became a {value:,.0f} Toman coupon: {coupon.code}",
        url="/rewards/",
    )
    return coupon
