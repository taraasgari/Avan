from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from apps.cart.models import Cart
from apps.notifications.models import Notification
from apps.orders.models import Order

from .models import AbandonedCartEvent, CommerceSettings, FulfillmentEvent, Refund, ShippingRule


def shipping_quote(*, method, subtotal, province="", city=""):
    subtotal = Decimal(subtotal or 0)
    base = Decimal(method.base_price or 0)
    settings_obj = CommerceSettings.load()
    if settings_obj.free_shipping_threshold is not None and subtotal >= settings_obj.free_shipping_threshold:
        return Decimal("0"), "global_free_shipping"

    qs = ShippingRule.objects.filter(method=method, is_active=True, minimum_subtotal__lte=subtotal)
    province = (province or "").strip()
    city = (city or "").strip()
    matching = []
    for rule in qs:
        if rule.maximum_subtotal is not None and subtotal > rule.maximum_subtotal:
            continue
        if rule.province and rule.province.casefold() != province.casefold():
            continue
        if rule.city and rule.city.casefold() != city.casefold():
            continue
        matching.append(rule)
    matching.sort(key=lambda r: (r.priority, -int(bool(r.city)), -int(bool(r.province)), r.id))
    if not matching:
        return base, "base"
    rule = matching[0]
    if rule.free_over is not None and subtotal >= rule.free_over:
        return Decimal("0"), f"rule:{rule.id}:free"
    if rule.price_override is not None:
        return Decimal(rule.price_override), f"rule:{rule.id}:override"
    return base, f"rule:{rule.id}:base"


def record_fulfillment(*, order, event, actor=None, from_status="", to_status="", note=""):
    return FulfillmentEvent.objects.create(
        order=order,
        event=event,
        actor=actor,
        from_status=from_status or "",
        to_status=to_status or "",
        note=(note or "")[:240],
    )


def cart_value(cart):
    total = Decimal("0")
    count = 0
    for item in cart.items.select_related("variant"):
        total += Decimal(item.unit_price_total) * item.quantity
        count += item.quantity
    return total, count


@transaction.atomic
def detect_abandoned_carts(*, now=None):
    now = now or timezone.now()
    config = CommerceSettings.load()
    cutoff = now - timedelta(hours=config.abandoned_cart_hours)
    created = 0
    recovered = 0

    stale = Cart.objects.filter(status=Cart.Status.OPEN, updated_at__lte=cutoff).prefetch_related("items__variant")
    for cart in stale:
        if not cart.items.exists():
            continue
        value, count = cart_value(cart)
        event, was_created = AbandonedCartEvent.objects.get_or_create(
            cart=cart,
            defaults={"item_count": count, "value_snapshot": value, "last_seen_at": cart.updated_at},
        )
        if was_created:
            created += 1
            if cart.user_id:
                Notification.objects.create(
                    user=cart.user,
                    kind=Notification.Kind.SYSTEM,
                    title="سبد خرید شما منتظر است",
                    body="آیتم‌های سبد خریدتان هنوز ذخیره هستند.",
                    url="/bag/",
                )
        elif event.status == AbandonedCartEvent.Status.DETECTED:
            event.item_count = count
            event.value_snapshot = value
            event.last_seen_at = cart.updated_at
            event.save(update_fields=["item_count", "value_snapshot", "last_seen_at"])

    detected = AbandonedCartEvent.objects.filter(status=AbandonedCartEvent.Status.DETECTED).select_related("cart")
    for event in detected:
        if event.cart.status == Cart.Status.CONVERTED or event.cart.updated_at > event.detected_at:
            event.status = AbandonedCartEvent.Status.RECOVERED
            event.recovered_at = now
            event.save(update_fields=["status", "recovered_at"])
            recovered += 1
    return {"created": created, "recovered": recovered}


@transaction.atomic
def create_refund(*, order, amount, actor=None, reason="", return_request=None):
    amount = Decimal(amount or 0)
    if amount <= 0:
        raise ValueError("Refund amount must be greater than zero.")
    paid = Decimal(order.total_amount or 0)
    already = order.refunds.filter(status=Refund.Status.SUCCEEDED).aggregate(v=Sum("amount"))["v"] or Decimal("0")
    if already + amount > paid:
        raise ValueError("Refund total cannot exceed the paid order total.")
    payment = order.payment_attempts.filter(status="succeeded").order_by("-created_at").first()
    return Refund.objects.create(
        order=order,
        return_request=return_request,
        payment_attempt=payment,
        amount=amount,
        provider=payment.provider if payment else "manual",
        reason=reason,
        requested_by=actor,
    )


@transaction.atomic
def approve_refund(*, refund, actor=None):
    refund = Refund.objects.select_for_update().select_related("order", "payment_attempt").get(pk=refund.pk)
    if refund.status not in {Refund.Status.REQUESTED, Refund.Status.FAILED}:
        return refund
    refund.status = Refund.Status.APPROVED
    refund.approved_by = actor
    refund.save(update_fields=["status", "approved_by", "updated_at"])
    return refund


@transaction.atomic
def complete_refund(*, refund, external_reference="", actor=None):
    refund = Refund.objects.select_for_update().select_related("order").get(pk=refund.pk)
    if refund.status == Refund.Status.SUCCEEDED:
        return refund
    refund.status = Refund.Status.SUCCEEDED
    refund.external_reference = external_reference or refund.external_reference
    refund.completed_at = timezone.now()
    refund.approved_by = refund.approved_by or actor
    refund.save(update_fields=["status", "external_reference", "completed_at", "approved_by", "updated_at"])
    record_fulfillment(order=refund.order, event="refund_succeeded", actor=actor, note=f"Refund {refund.amount}")
    if refund.order.user_id:
        Notification.objects.create(
            user=refund.order.user,
            kind=Notification.Kind.ORDER,
            title="بازگشت وجه ثبت شد",
            body=f"بازگشت وجه سفارش {refund.order.number} ثبت شد.",
            url=f"/orders/{refund.order.number}/",
        )
    return refund
