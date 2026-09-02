from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.shortcuts import render
from django.utils import timezone

from apps.cart.models import Cart
from apps.catalog.models import ProductVariant
from apps.operations.models import ReturnRequest, Shipment
from apps.orders.models import Order, OrderItem

from .decorators import owner_required
from .models import OwnerSettings


User = get_user_model()
PAID_STATUSES = [
    Order.Status.PAID,
    Order.Status.PROCESSING,
    Order.Status.SHIPPED,
    Order.Status.DELIVERED,
]


def _owner_context(request, **extra):
    from .views import _owner_context as base_context

    return base_context(request, **extra)


@owner_required
def analytics(request):
    today = timezone.localdate()
    start = today - timedelta(days=29)

    raw_daily = {
        row["day"]: {
            "orders": row["orders"],
            "revenue": int(row["revenue"] or 0),
        }
        for row in (
            Order.objects.filter(created_at__date__gte=start, created_at__date__lte=today)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(
                orders=Count("id"),
                revenue=Coalesce(
                    Sum("total_amount", filter=Q(status__in=PAID_STATUSES)),
                    Decimal("0"),
                ),
            )
            .order_by("day")
        )
    }

    daily = []
    for offset in range(30):
        day = start + timedelta(days=offset)
        point = raw_daily.get(day, {"orders": 0, "revenue": 0})
        daily.append({
            "label": day.strftime("%m/%d"),
            "date": day.isoformat(),
            "orders": int(point["orders"]),
            "revenue": int(point["revenue"]),
        })

    order_status = [
        {"status": row["status"], "count": row["count"]}
        for row in Order.objects.values("status").annotate(count=Count("id")).order_by("status")
    ]
    cart_status = [
        {"status": row["status"], "count": row["count"]}
        for row in Cart.objects.values("status").annotate(count=Count("id")).order_by("status")
    ]
    shipping_status = [
        {"status": row["status"], "count": row["count"]}
        for row in Shipment.objects.values("status").annotate(count=Count("id")).order_by("status")
    ]

    top_products = list(
        OrderItem.objects.filter(order__status__in=PAID_STATUSES)
        .values("product_name")
        .annotate(quantity=Coalesce(Sum("quantity"), 0), revenue=Coalesce(Sum("line_total"), Decimal("0")))
        .order_by("-quantity")[:10]
    )

    total_revenue = Order.objects.filter(status__in=PAID_STATUSES).aggregate(
        value=Coalesce(Sum("total_amount"), Decimal("0"))
    )["value"]
    paid_orders = Order.objects.filter(status__in=PAID_STATUSES).count()
    average_order = (total_revenue / paid_orders).quantize(Decimal("1")) if paid_orders else Decimal("0")

    month_revenue = Order.objects.filter(
        status__in=PAID_STATUSES,
        paid_at__date__gte=start,
    ).aggregate(value=Coalesce(Sum("total_amount"), Decimal("0")))["value"]

    new_customers = User.objects.filter(date_joined__date__gte=start, is_superuser=False).count()
    returns_open = ReturnRequest.objects.exclude(
        status__in=[ReturnRequest.Status.REJECTED, ReturnRequest.Status.REFUNDED, ReturnRequest.Status.CLOSED]
    ).count()
    low_threshold = OwnerSettings.load().low_stock_threshold
    low_stock_count = ProductVariant.objects.filter(is_active=True, stock__lte=low_threshold).count()

    chart_data = {
        "daily": daily,
        "order_status": order_status,
        "cart_status": cart_status,
        "shipping_status": shipping_status,
    }

    return render(
        request,
        "owner/analytics.html",
        _owner_context(
            request,
            total_revenue=total_revenue,
            month_revenue=month_revenue,
            paid_orders=paid_orders,
            average_order=average_order,
            new_customers=new_customers,
            returns_open=returns_open,
            low_stock_count=low_stock_count,
            top_products=top_products,
            chart_data=chart_data,
        ),
    )
