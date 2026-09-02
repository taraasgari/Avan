from decimal import Decimal, ROUND_DOWN
from django.utils import timezone

from .models import Coupon, CouponRedemption


def validate_coupon(coupon: Coupon | None, *, user=None, subtotal=None):
    if coupon is None:
        return True, ""
    now = timezone.now()
    if not coupon.is_active:
        return False, "Coupon is inactive."
    if coupon.starts_at and coupon.starts_at > now:
        return False, "Coupon is not active yet."
    if coupon.ends_at and coupon.ends_at <= now:
        return False, "Coupon has expired."
    if coupon.usage_limit is not None and coupon.redemptions.count() >= coupon.usage_limit:
        return False, "Coupon usage limit has been reached."
    if user and user.is_authenticated:
        used = CouponRedemption.objects.filter(coupon=coupon, user=user).count()
        if used >= coupon.usage_limit_per_user:
            return False, "You have already used this coupon."
    if subtotal is not None and Decimal(subtotal) < coupon.minimum_subtotal:
        return False, "Cart subtotal is below the coupon minimum."
    return True, ""


def calculate_coupon_discount(coupon: Coupon | None, *, subtotal, user=None):
    subtotal = Decimal(subtotal)
    valid, _ = validate_coupon(coupon, user=user, subtotal=subtotal)
    if not valid or coupon is None:
        return Decimal("0")
    if coupon.discount_type == Coupon.DiscountType.PERCENT:
        discount = (subtotal * coupon.value / Decimal("100")).quantize(Decimal("1"), rounding=ROUND_DOWN)
    else:
        discount = coupon.value
    if coupon.maximum_discount is not None:
        discount = min(discount, coupon.maximum_discount)
    return min(subtotal, max(Decimal("0"), discount))
