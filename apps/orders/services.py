import uuid
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.cart.models import Cart
from apps.coupons.models import CouponRedemption
from apps.coupons.services import calculate_coupon_discount, validate_coupon
from apps.payments.models import PaymentAttempt
from apps.notifications.models import Notification
from .models import Order, OrderItem, StockReservation


class CheckoutError(Exception):
    pass


def reservation_minutes():
    return int(getattr(settings, "ORDER_RESERVATION_MINUTES", 20))


@transaction.atomic
def place_order(*, cart: Cart, checkout_data: dict, idempotency_key=None, user=None):
    if idempotency_key:
        try:
            idempotency_key = uuid.UUID(str(idempotency_key))
        except ValueError as exc:
            raise CheckoutError("Invalid idempotency key.") from exc
        existing = Order.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing, False
    else:
        idempotency_key = uuid.uuid4()

    if cart.status != Cart.Status.OPEN:
        raise CheckoutError("Cart is not open.")
    if not cart.items.exists():
        raise CheckoutError("Cart is empty.")

    items = list(cart.items.select_related("variant__product", "variant__color", "variant__size"))
    variant_ids = sorted({item.variant_id for item in items})
    from apps.catalog.models import ProductVariant
    locked_variants = {
        v.id: v for v in ProductVariant.objects.select_for_update().select_related("product", "color", "size").filter(id__in=variant_ids)
    }
    now = timezone.now()
    StockReservation.objects.filter(
        variant_id__in=variant_ids,
        status=StockReservation.Status.ACTIVE,
        expires_at__lte=now,
    ).update(status=StockReservation.Status.RELEASED)

    subtotal = Decimal("0")
    for item in items:
        variant = locked_variants.get(item.variant_id)
        if not variant or not variant.is_active or not variant.product.is_active:
            raise CheckoutError("One of the selected products is unavailable.")
        reserved = sum(
            StockReservation.objects.filter(
                variant=variant,
                status=StockReservation.Status.ACTIVE,
                expires_at__gt=now,
            ).values_list("quantity", flat=True)
        )
        available = int(variant.stock) - reserved
        if item.quantity > available:
            raise CheckoutError(f"Not enough stock for SKU {variant.sku}.")
        subtotal += Decimal(variant.price) * item.quantity

    valid, message = validate_coupon(cart.coupon, user=user, subtotal=subtotal)
    if not valid:
        raise CheckoutError(message)
    discount = calculate_coupon_discount(cart.coupon, subtotal=subtotal, user=user)
    shipping = Decimal(str(getattr(settings, "DEFAULT_SHIPPING_AMOUNT", 0)))
    total = max(Decimal("0"), subtotal - discount + shipping)

    order = Order.objects.create(
        idempotency_key=idempotency_key,
        user=user if user and user.is_authenticated else None,
        cart=cart,
        subtotal=subtotal,
        discount_amount=discount,
        shipping_amount=shipping,
        total_amount=total,
        customer_name=checkout_data["customer_name"],
        phone=checkout_data["phone"],
        email=checkout_data.get("email", ""),
        province=checkout_data["province"],
        city=checkout_data["city"],
        address=checkout_data["address"],
        postal_code=checkout_data.get("postal_code", ""),
        customer_note=checkout_data.get("customer_note", ""),
    )

    expires_at = now + timedelta(minutes=reservation_minutes())
    for item in items:
        variant = locked_variants[item.variant_id]
        snapshot = item.design_snapshot or {}
        OrderItem.objects.create(
            order=order,
            variant=variant,
            product_name=variant.product.name,
            sku=variant.sku,
            color_name=variant.color.name,
            size_name=variant.size.name,
            unit_price=variant.price,
            quantity=item.quantity,
            line_total=Decimal(variant.price) * item.quantity,
            is_customized=bool(item.design_id or snapshot),
            design_id_snapshot=item.design_id,
            design_title=snapshot.get("title", "")[:120],
            design_owner_name=snapshot.get("owner_name", "")[:120],
            design_snapshot=snapshot,
        )
        StockReservation.objects.create(order=order, variant=variant, quantity=item.quantity, expires_at=expires_at)

    PaymentAttempt.objects.create(order=order, amount=total, provider="pending")
    if order.user_id:
        Notification.objects.create(
            user=order.user,
            kind=Notification.Kind.ORDER,
            title="سفارش ثبت شد",
            body=f"سفارش {order.number} ثبت شد و منتظر پرداخت است.",
            url=f"/orders/{order.number}/",
        )
    cart.status = Cart.Status.CONVERTED
    cart.save(update_fields=["status", "updated_at"])
    return order, True


@transaction.atomic
def release_order(order: Order):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status == Order.Status.PAID:
        return order
    order.reservations.filter(status=StockReservation.Status.ACTIVE).update(status=StockReservation.Status.RELEASED)
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status", "updated_at"])
    return order


@transaction.atomic
def confirm_payment(order: Order, payment_attempt: PaymentAttempt, *, external_reference=""):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status == Order.Status.PAID:
        return order
    reservations = list(order.reservations.select_for_update().select_related("variant"))
    active = [r for r in reservations if r.status == StockReservation.Status.ACTIVE]
    if len(active) != len(reservations):
        order.status = Order.Status.NEEDS_REVIEW
        order.save(update_fields=["status", "updated_at"])
        payment_attempt.status = PaymentAttempt.Status.REQUIRES_REVIEW
        payment_attempt.external_reference = external_reference
        payment_attempt.save(update_fields=["status", "external_reference", "updated_at"])
        return order

    from apps.catalog.models import ProductVariant
    variant_ids = sorted(r.variant_id for r in active)
    variants = {v.id: v for v in ProductVariant.objects.select_for_update().filter(id__in=variant_ids)}
    for reservation in active:
        variant = variants[reservation.variant_id]
        if variant.stock < reservation.quantity:
            order.status = Order.Status.NEEDS_REVIEW
            order.save(update_fields=["status", "updated_at"])
            payment_attempt.status = PaymentAttempt.Status.REQUIRES_REVIEW
            payment_attempt.external_reference = external_reference
            payment_attempt.save(update_fields=["status", "external_reference", "updated_at"])
            return order

    for reservation in active:
        variant = variants[reservation.variant_id]
        variant.stock -= reservation.quantity
        variant.save(update_fields=["stock"])
        reservation.status = StockReservation.Status.CONSUMED
        reservation.save(update_fields=["status"])

    order.status = Order.Status.PAID
    order.paid_at = timezone.now()
    order.save(update_fields=["status", "paid_at", "updated_at"])
    payment_attempt.status = PaymentAttempt.Status.SUCCEEDED
    payment_attempt.external_reference = external_reference
    payment_attempt.save(update_fields=["status", "external_reference", "updated_at"])
    if order.cart and order.cart.coupon:
        CouponRedemption.objects.get_or_create(coupon=order.cart.coupon, user=order.user, order=order)
    if order.user_id:
        Notification.objects.create(
            user=order.user,
            kind=Notification.Kind.ORDER,
            title="پرداخت موفق",
            body=f"پرداخت سفارش {order.number} با موفقیت ثبت شد.",
            url=f"/orders/{order.number}/",
        )
    return order
