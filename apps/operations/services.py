from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import ProductVariant
from apps.orders.models import Order

from .models import InventoryMovement, Shipment


@transaction.atomic
def adjust_stock(*, variant_id, delta, kind, actor=None, note=""):
    variant = ProductVariant.objects.select_for_update().get(pk=variant_id)
    before = int(variant.stock)
    after = before + int(delta)
    if after < 0:
        raise ValidationError("Stock cannot become negative.")
    variant.stock = after
    variant.save(update_fields=["stock"])
    movement = InventoryMovement.objects.create(
        variant=variant,
        kind=kind,
        delta=int(delta),
        stock_before=before,
        stock_after=after,
        actor=actor if actor and actor.is_authenticated else None,
        note=note[:240],
    )
    return movement


@transaction.atomic
def update_shipment(*, shipment, cleaned_data):
    shipment = Shipment.objects.select_for_update().select_related("order").get(pk=shipment.pk)
    old_status = shipment.status
    for field, value in cleaned_data.items():
        setattr(shipment, field, value)

    if shipment.status == Shipment.Status.SHIPPED and old_status != Shipment.Status.SHIPPED:
        shipment.shipped_at = timezone.now()
        if shipment.order.status in {Order.Status.PAID, Order.Status.PROCESSING}:
            shipment.order.status = Order.Status.SHIPPED
            shipment.order.save(update_fields=["status", "updated_at"])

    if shipment.status == Shipment.Status.DELIVERED and old_status != Shipment.Status.DELIVERED:
        shipment.delivered_at = timezone.now()
        if shipment.order.status == Order.Status.SHIPPED:
            shipment.order.status = Order.Status.DELIVERED
            shipment.order.save(update_fields=["status", "updated_at"])

    shipment.save()
    return shipment
