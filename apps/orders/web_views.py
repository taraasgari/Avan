from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from apps.operations.models import Address, ShippingMethod

from .models import Order


def checkout_page(request):
    addresses = Address.objects.none()
    if request.user.is_authenticated:
        addresses = Address.objects.filter(user=request.user)
    methods = ShippingMethod.objects.filter(is_active=True).order_by("sort_order", "id")
    return render(
        request,
        "orders/checkout.html",
        {
            "saved_addresses": addresses,
            "shipping_methods": methods,
        },
    )


def order_detail_page(request, number):
    order = get_object_or_404(
        Order.objects.select_related("user").prefetch_related("items", "payment_attempts"),
        number=number,
    )
    if order.user_id and (not request.user.is_authenticated or request.user.id != order.user_id):
        # Preserve the same privacy rule as the API without leaking whether the order exists.
        from django.http import Http404

        raise Http404
    payment = order.payment_attempts.order_by("-created_at").first()
    try:
        shipment = order.shipment
    except Exception:
        shipment = None
    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
            "payment": payment,
            "shipment": shipment,
            "debug_payment": bool(settings.DEBUG),
        },
    )


def _shipment_for(order):
    try:
        return order.shipment
    except Exception:
        return None

def track_order_page(request):
    code = (request.GET.get("code") or request.POST.get("code") or "").strip().upper()[:64]
    contact = (request.GET.get("contact") or request.POST.get("contact") or "").strip()[:120]
    order = None
    error = ""
    if code:
        qs = Order.objects.select_related("user").prefetch_related("items")
        if request.user.is_authenticated:
            order = qs.filter(Q(tracking_code__iexact=code) | Q(items__item_tracking_code__iexact=code), user=request.user).distinct().first()
        else:
            if not contact:
                error = "برای مشاهده وضعیت، ایمیل یا موبایل سفارش را هم وارد کنید."
            else:
                order = qs.filter(Q(tracking_code__iexact=code) | Q(items__item_tracking_code__iexact=code)).filter(Q(email__iexact=contact) | Q(phone=contact)).distinct().first()
        if not order and not error:
            error = "سفارشی با این مشخصات پیدا نشد."
    return render(request, "orders/track.html", {"tracked_order": order, "tracked_shipment": _shipment_for(order) if order else None, "tracking_code_query": code, "tracking_contact": contact, "tracking_error": error})
