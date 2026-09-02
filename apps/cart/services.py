from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.coupons.services import calculate_coupon_discount
from apps.orders.models import StockReservation
from .models import Cart


def reserved_quantity_for_variant(variant_id: int) -> int:
    now = timezone.now()
    total = (
        StockReservation.objects.filter(
            variant_id=variant_id,
            status=StockReservation.Status.ACTIVE,
            expires_at__gt=now,
        )
        .values_list("quantity", flat=True)
    )
    return sum(total)


def available_stock(variant) -> int:
    return max(0, int(variant.stock) - reserved_quantity_for_variant(variant.id))


def cart_totals(cart: Cart) -> dict:
    items = list(
        cart.items.select_related("variant__product", "variant__color", "variant__size")
    )
    subtotal = sum((item.unit_price_total * item.quantity for item in items), Decimal("0"))
    discount = calculate_coupon_discount(cart.coupon, subtotal=subtotal, user=cart.user)
    total = max(Decimal("0"), subtotal - discount)
    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping": Decimal("0"),
        "total": total,
    }


def get_open_cart(token):
    return Cart.objects.get(token=token, status=Cart.Status.OPEN)


@transaction.atomic
def apply_coupon(cart: Cart, coupon):
    cart.coupon = coupon
    cart.save(update_fields=["coupon", "updated_at"])
    return cart_totals(cart)
