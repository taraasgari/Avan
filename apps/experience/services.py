from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.coupons.models import Coupon
from apps.notifications.models import Notification
from .models import RewardTransaction, RewardWallet


@transaction.atomic
def grant_points(*, user, amount, reason, reference=None):
    if amount <= 0:
        raise ValueError("Reward amount must be positive.")

    wallet, _ = RewardWallet.objects.select_for_update().get_or_create(user=user)

    if reference:
        existing = RewardTransaction.objects.filter(reference=reference).first()
        if existing:
            return existing, False

    entry = RewardTransaction.objects.create(
        wallet=wallet,
        amount=amount,
        reason=reason,
        reference=reference,
    )
    wallet.balance += amount
    wallet.save(update_fields=["balance", "updated_at"])

    Notification.objects.create(
        user=user,
        kind=Notification.Kind.REWARD,
        title="AVAN Points added",
        body=f"You earned {amount} AVAN Points — {reason}",
        url="/rewards/",
    )

    return entry, True


def _coupon_code(prefix, entry_id, user_id, suffix):
    return f"{prefix}-{entry_id}-{user_id}-{suffix}"[:40].upper()


@transaction.atomic
def grant_challenge_entry_reward(entry):
    challenge = entry.challenge
    user = entry.user
    granted_any = False

    if challenge.reward_points > 0:
        _, created = grant_points(
            user=user,
            amount=challenge.reward_points,
            reason=f"{challenge.title} — winner reward",
            reference=f"challenge-winner:{entry.id}:points",
        )
        granted_any = granted_any or created

    expires_at = timezone.now() + timedelta(days=max(1, challenge.reward_expiry_days))

    if challenge.reward_discount_percent > 0:
        _, created = Coupon.objects.get_or_create(
            code=_coupon_code("CHAL-D", entry.id, user.id, "WIN"),
            defaults={
                "discount_type": Coupon.DiscountType.PERCENT,
                "value": min(Decimal("100"), Decimal(challenge.reward_discount_percent)),
                "assigned_user": user,
                "usage_limit": 1,
                "usage_limit_per_user": 1,
                "ends_at": expires_at,
                "is_active": True,
            },
        )
        granted_any = granted_any or created

    if challenge.reward_subsidy_amount > 0:
        _, created = Coupon.objects.get_or_create(
            code=_coupon_code("CHAL-C", entry.id, user.id, "WIN"),
            defaults={
                "discount_type": Coupon.DiscountType.FIXED,
                "value": challenge.reward_subsidy_amount,
                "assigned_user": user,
                "usage_limit": 1,
                "usage_limit_per_user": 1,
                "ends_at": expires_at,
                "is_active": True,
            },
        )
        granted_any = granted_any or created

    if granted_any:
        Notification.objects.create(
            user=user,
            kind=Notification.Kind.REWARD,
            title="Challenge reward unlocked",
            body=f"Your reward for winning {challenge.title} is ready in My Rewards.",
            url="/rewards/",
        )
    return granted_any
