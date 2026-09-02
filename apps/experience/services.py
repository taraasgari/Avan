from django.db import transaction

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
