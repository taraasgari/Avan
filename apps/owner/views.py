import csv
import uuid
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.catalog.models import Category, Color, Product, ProductVariant, Size
from apps.coupons.models import Coupon
from apps.designs.models import Design
from apps.experience.models import Challenge, Drop, RewardWallet
from apps.marketplace.models import CreatorEarning, CreatorWallet, MarketplaceSettings, PayoutRequest
from apps.marketplace.services import approve_payout, mark_payout_paid, reject_payout
from apps.notifications.models import Notification
from apps.orders.models import Order, OrderItem, StockReservation
from apps.orders.services import release_order
from apps.payments.models import PaymentAttempt

from .decorators import owner_required, superuser_required
from .forms import MarketplaceSettingsForm, OwnerSettingsForm, ProductForm
from .models import OwnerSettings


User = get_user_model()
PAID_STATUSES = [
    Order.Status.PAID,
    Order.Status.PROCESSING,
    Order.Status.SHIPPED,
    Order.Status.DELIVERED,
]


def _owner_context(request, **extra):
    settings_obj = OwnerSettings.load()
    try:
        from apps.launchops.permissions import get_staff_access
        owner_access = get_staff_access(request.user)
    except Exception:
        owner_access = None
    context = {
        "owner_settings": settings_obj,
        "owner_access": owner_access,
        "owner_pending_orders": Order.objects.filter(status=Order.Status.PENDING_PAYMENT).count(),
        "owner_review_orders": Order.objects.filter(status=Order.Status.NEEDS_REVIEW).count(),
        "owner_pending_payouts": PayoutRequest.objects.filter(status=PayoutRequest.Status.PENDING).count(),
    }
    context.update(extra)
    return context


@owner_required
def dashboard(request):
    today = timezone.localdate()
    low_threshold = OwnerSettings.load().low_stock_threshold

    revenue = (
        Order.objects.filter(status__in=PAID_STATUSES)
        .aggregate(total=Coalesce(Sum("total_amount"), Decimal("0")))
        ["total"]
    )
    today_revenue = (
        Order.objects.filter(status__in=PAID_STATUSES, paid_at__date=today)
        .aggregate(total=Coalesce(Sum("total_amount"), Decimal("0")))
        ["total"]
    )
    today_orders = Order.objects.filter(created_at__date=today).count()
    low_stock = ProductVariant.objects.filter(is_active=True, stock__lte=low_threshold).select_related(
        "product", "color", "size"
    ).order_by("stock")[:8]

    top_products = (
        OrderItem.objects.filter(order__status__in=PAID_STATUSES)
        .values("product_name")
        .annotate(quantity=Sum("quantity"), revenue=Sum("line_total"))
        .order_by("-quantity")[:6]
    )

    context = _owner_context(
        request,
        revenue=revenue,
        today_revenue=today_revenue,
        today_orders=today_orders,
        total_orders=Order.objects.count(),
        customers_count=User.objects.filter(is_superuser=False).count(),
        products_count=Product.objects.count(),
        active_products_count=Product.objects.filter(is_active=True).count(),
        published_designs=Design.objects.filter(status=Design.Status.PUBLISHED).count(),
        creators_count=User.objects.filter(public_profile_enabled=True).count(),
        pending_payout_total=(
            PayoutRequest.objects.filter(status__in=[PayoutRequest.Status.PENDING, PayoutRequest.Status.APPROVED])
            .aggregate(total=Coalesce(Sum("amount"), Decimal("0")))
            ["total"]
        ),
        low_stock=low_stock,
        low_stock_count=ProductVariant.objects.filter(is_active=True, stock__lte=low_threshold).count(),
        recent_orders=Order.objects.select_related("user").order_by("-created_at")[:8],
        top_products=top_products,
    )
    return render(request, "owner/dashboard.html", context)


@owner_required
def products(request):
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    state = request.GET.get("state", "").strip()

    qs = Product.objects.select_related("category").prefetch_related("variants", "images").order_by("-updated_at")
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(slug__icontains=q) | Q(variants__sku__icontains=q)).distinct()
    if category:
        qs = qs.filter(category_id=category)
    if state == "active":
        qs = qs.filter(is_active=True)
    elif state == "inactive":
        qs = qs.filter(is_active=False)
    elif state == "featured":
        qs = qs.filter(is_featured=True)

    return render(
        request,
        "owner/products.html",
        _owner_context(
            request,
            products=qs[:150],
            categories=Category.objects.order_by("sort_order", "name"),
            query=q,
            selected_category=category,
            selected_state=state,
        ),
    )


@owner_required
def product_edit(request, product_id=None):
    product = get_object_or_404(Product, pk=product_id) if product_id else None
    form = ProductForm(request.POST or None, instance=product)
    if request.method == "POST" and form.is_valid():
        product = form.save()
        messages.success(request, "Product saved.")
        return redirect("owner:product-edit", product_id=product.id)

    variants = product.variants.select_related("color", "size").order_by("color__name", "size__sort_order") if product else []
    images = product.images.all() if product else []
    return render(
        request,
        "owner/product_form.html",
        _owner_context(request, form=form, product=product, variants=variants, images=images),
    )


@owner_required
def warehouse(request):
    q = request.GET.get("q", "").strip()
    stock_filter = request.GET.get("stock", "").strip()
    low_threshold = OwnerSettings.load().low_stock_threshold

    if request.method == "POST":
        variant = get_object_or_404(ProductVariant.objects.select_related("product"), pk=request.POST.get("variant_id"))
        try:
            new_stock = int(request.POST.get("stock", variant.stock))
            if new_stock < 0:
                raise ValueError
        except (TypeError, ValueError):
            messages.error(request, "Stock must be zero or more.")
            return redirect("owner:warehouse")

        active_reserved = sum(
            StockReservation.objects.filter(
                variant=variant,
                status=StockReservation.Status.ACTIVE,
                expires_at__gt=timezone.now(),
            ).values_list("quantity", flat=True)
        )
        if new_stock < active_reserved:
            messages.error(
                request,
                f"Cannot set stock below {active_reserved}; that quantity is currently reserved by open orders.",
            )
            return redirect("owner:warehouse")

        price_override_raw = request.POST.get("price_override", "").strip()
        price_override = None
        if price_override_raw:
            try:
                price_override = Decimal(price_override_raw)
                if price_override < 0 or price_override != price_override.quantize(Decimal("1")):
                    raise ValueError
            except Exception:
                messages.error(request, "Price override must be a non-negative whole Toman amount.")
                return redirect("owner:warehouse")

        variant.stock = new_stock
        variant.price_override = price_override
        variant.is_active = request.POST.get("is_active") == "on"
        variant.save(update_fields=["stock", "price_override", "is_active"])
        messages.success(request, f"{variant.sku} updated.")
        return redirect("owner:warehouse")

    qs = ProductVariant.objects.select_related("product", "color", "size").order_by("product__name", "color__name", "size__sort_order")
    if q:
        qs = qs.filter(Q(product__name__icontains=q) | Q(sku__icontains=q) | Q(color__name__icontains=q) | Q(size__name__icontains=q))
    if stock_filter == "out":
        qs = qs.filter(stock=0)
    elif stock_filter == "low":
        qs = qs.filter(stock__gt=0, stock__lte=low_threshold)
    elif stock_filter == "in":
        qs = qs.filter(stock__gt=low_threshold)

    rows = []
    for variant in qs[:250]:
        rows.append({
            "variant": variant,
            "available": variant.available_stock,
            "is_low": variant.stock <= low_threshold,
        })

    return render(
        request,
        "owner/warehouse.html",
        _owner_context(
            request,
            rows=rows,
            query=q,
            stock_filter=stock_filter,
            low_threshold=low_threshold,
            total_stock=ProductVariant.objects.aggregate(total=Coalesce(Sum("stock"), 0))["total"],
            out_count=ProductVariant.objects.filter(stock=0).count(),
            low_count=ProductVariant.objects.filter(stock__gt=0, stock__lte=low_threshold).count(),
        ),
    )


@owner_required
def orders(request):
    q = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    qs = Order.objects.select_related("user").prefetch_related("items").order_by("-created_at")
    if status_filter:
        qs = qs.filter(status=status_filter)
    if q:
        order_number = None
        try:
            order_number = uuid.UUID(q)
        except (TypeError, ValueError):
            pass
        query = Q(customer_name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q)
        if order_number:
            query |= Q(number=order_number)
        qs = qs.filter(query)

    return render(
        request,
        "owner/orders.html",
        _owner_context(request, orders=qs[:200], statuses=Order.Status.choices, query=q, selected_status=status_filter),
    )


def _allowed_order_transitions(order):
    mapping = {
        Order.Status.PENDING_PAYMENT: [Order.Status.CANCELLED, Order.Status.NEEDS_REVIEW],
        Order.Status.PAID: [Order.Status.PROCESSING, Order.Status.NEEDS_REVIEW],
        Order.Status.PROCESSING: [Order.Status.SHIPPED, Order.Status.NEEDS_REVIEW],
        Order.Status.SHIPPED: [Order.Status.DELIVERED, Order.Status.NEEDS_REVIEW],
        Order.Status.NEEDS_REVIEW: [Order.Status.PROCESSING, Order.Status.CANCELLED],
    }
    return mapping.get(order.status, [])


@owner_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("user", "cart").prefetch_related("items__variant", "payment_attempts", "reservations__variant"),
        pk=order_id,
    )
    if request.method == "POST":
        next_status = request.POST.get("status", "")
        allowed = _allowed_order_transitions(order)
        if next_status not in allowed:
            messages.error(request, "That status transition is blocked to protect payment and stock integrity.")
        elif next_status == Order.Status.CANCELLED:
            release_order(order)
            messages.success(request, "Order cancelled and active stock reservations released.")
        else:
            order.status = next_status
            order.save(update_fields=["status", "updated_at"])
            messages.success(request, "Order status updated.")
        return redirect("owner:order-detail", order_id=order.id)

    return render(
        request,
        "owner/order_detail.html",
        _owner_context(request, order=order, allowed_statuses=_allowed_order_transitions(order)),
    )


@owner_required
def customers(request):
    q = request.GET.get("q", "").strip()
    qs = User.objects.annotate(
        order_count=Count("orders", distinct=True),
        paid_total=Coalesce(Sum("orders__total_amount", filter=Q(orders__status__in=PAID_STATUSES)), Decimal("0")),
    ).order_by("-date_joined")
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(display_name__icontains=q))
    return render(request, "owner/customers.html", _owner_context(request, customers=qs[:200], query=q))


@owner_required
def customer_detail(request, user_id):
    customer = get_object_or_404(User, pk=user_id)
    order_qs = customer.orders.prefetch_related("items").order_by("-created_at")
    paid_total = order_qs.filter(status__in=PAID_STATUSES).aggregate(total=Coalesce(Sum("total_amount"), Decimal("0")))["total"]
    return render(
        request,
        "owner/customer_detail.html",
        _owner_context(
            request,
            customer=customer,
            customer_orders=order_qs[:30],
            paid_total=paid_total,
            designs=customer.designs.select_related("base_product").order_by("-updated_at")[:12],
            notifications=customer.notifications.order_by("-created_at")[:12],
        ),
    )


@require_POST
@owner_required
def customer_toggle_active(request, user_id):
    customer = get_object_or_404(User, pk=user_id)
    if customer.pk == request.user.pk or customer.is_superuser:
        messages.error(request, "Owner/superuser accounts cannot be disabled here.")
    else:
        customer.is_active = not customer.is_active
        customer.save(update_fields=["is_active"])
        messages.success(request, "Customer account status updated.")
    return redirect("owner:customer-detail", user_id=customer.id)


@owner_required
def designs(request):
    q = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    qs = Design.objects.select_related("owner", "base_product", "base_color").annotate(
        like_count=Count("likes", distinct=True),
        remix_count=Count("remixes", distinct=True),
    ).order_by("-updated_at")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(owner__username__icontains=q) | Q(owner__display_name__icontains=q))
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(
        request,
        "owner/designs.html",
        _owner_context(request, designs=qs[:200], statuses=Design.Status.choices, query=q, selected_status=status_filter),
    )


@require_POST
@owner_required
def design_moderate(request, design_id):
    design = get_object_or_404(Design, pk=design_id)
    action = request.POST.get("action")
    if action == "hide":
        design.status = Design.Status.DRAFT
        design.visibility = Design.Visibility.PRIVATE
        design.is_for_sale = False
        design.save(update_fields=["status", "visibility", "is_for_sale", "updated_at"])
        messages.success(request, "Design removed from public Explore.")
    elif action == "publish":
        design.publish()
        messages.success(request, "Design published.")
    elif action == "disable_remix":
        design.allow_remix = False
        design.save(update_fields=["allow_remix", "updated_at"])
        messages.success(request, "Remix disabled for this design.")
    else:
        messages.error(request, "Unknown moderation action.")
    return redirect("owner:designs")


@owner_required
def creators(request):
    q = request.GET.get("q", "").strip()
    qs = User.objects.filter(Q(designs__isnull=False) | Q(public_profile_enabled=True)).distinct().annotate(
        designs_count=Count("designs", distinct=True),
        followers_count=Count("creator_followers", distinct=True),
    ).order_by("-date_joined")
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(display_name__icontains=q) | Q(email__icontains=q))

    rows = []
    for creator in qs[:150]:
        wallet = CreatorWallet.objects.filter(creator=creator).first()
        rows.append({"creator": creator, "wallet": wallet})
    return render(request, "owner/creators.html", _owner_context(request, rows=rows, query=q))


@owner_required
def marketing(request):
    return render(
        request,
        "owner/marketing.html",
        _owner_context(
            request,
            coupons=Coupon.objects.select_related("assigned_user").order_by("-created_at")[:80],
            drops=Drop.objects.order_by("-created_at")[:50],
            challenges=Challenge.objects.order_by("-created_at")[:50],
        ),
    )


@owner_required
def finance(request):
    earnings_total = CreatorEarning.objects.aggregate(total=Coalesce(Sum("creator_amount"), Decimal("0")))["total"]
    commission_total = CreatorEarning.objects.aggregate(total=Coalesce(Sum("platform_commission"), Decimal("0")))["total"]
    wallets = CreatorWallet.objects.select_related("creator").order_by("-total_earned")[:100]
    payouts = PayoutRequest.objects.select_related("creator").order_by("-requested_at")[:100]
    return render(
        request,
        "owner/finance.html",
        _owner_context(
            request,
            earnings_total=earnings_total,
            commission_total=commission_total,
            wallets=wallets,
            payouts=payouts,
            marketplace_settings=MarketplaceSettings.load(),
        ),
    )


@require_POST
@owner_required
def payout_action(request, payout_id):
    payout = get_object_or_404(PayoutRequest, pk=payout_id)
    action = request.POST.get("action")
    note = request.POST.get("admin_note", "")
    try:
        if action == "approve":
            _, changed = approve_payout(payout)
        elif action == "reject":
            _, changed = reject_payout(payout, admin_note=note)
        elif action == "paid":
            _, changed = mark_payout_paid(payout, admin_note=note)
        else:
            changed = False
        if changed:
            messages.success(request, "Payout updated.")
        else:
            messages.error(request, "Payout could not move to that state.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("owner:finance")


@superuser_required
def staff(request):
    from apps.launchops.models import StaffAccess

    staff_users = list(User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).order_by("-is_superuser", "username"))
    access_map = {obj.user_id: obj for obj in StaffAccess.objects.filter(user_id__in=[u.id for u in staff_users])}
    staff_rows = [{"user": user, "access": access_map.get(user.id)} for user in staff_users]
    other_users = User.objects.filter(is_staff=False, is_superuser=False, is_active=True).order_by("username")[:100]
    return render(
        request,
        "owner/staff.html",
        _owner_context(request, staff_rows=staff_rows, other_users=other_users, role_choices=StaffAccess.Role.choices),
    )


@require_POST
@superuser_required
def staff_toggle(request, user_id):
    from apps.launchops.models import StaffAccess

    user = get_object_or_404(User, pk=user_id)
    if user.is_superuser:
        messages.error(request, "Superuser access cannot be changed from this panel.")
    elif user.pk == request.user.pk:
        messages.error(request, "You cannot change your own owner access here.")
    else:
        user.is_staff = not user.is_staff
        user.save(update_fields=["is_staff"])
        if user.is_staff:
            access, _ = StaffAccess.objects.get_or_create(user=user)
            access.apply_role_preset(StaffAccess.Role.SUPPORT)
            access.updated_by = request.user
            access.save()
        else:
            StaffAccess.objects.filter(user=user).delete()
        messages.success(request, "Staff access updated.")
    return redirect("owner:staff")


@require_POST
@superuser_required
def staff_access_update(request, user_id):
    from apps.launchops.models import StaffAccess

    user = get_object_or_404(User, pk=user_id, is_staff=True, is_superuser=False)
    access, _ = StaffAccess.objects.get_or_create(user=user)
    role = request.POST.get("role", StaffAccess.Role.CUSTOM)
    valid_roles = {value for value, _ in StaffAccess.Role.choices}
    if role not in valid_roles:
        role = StaffAccess.Role.CUSTOM

    permission_fields = [
        "can_view_dashboard", "can_view_analytics", "can_manage_catalog",
        "can_manage_inventory", "can_manage_orders", "can_manage_customers",
        "can_manage_designs", "can_manage_marketing", "can_manage_finance",
        "can_manage_content", "can_manage_reports", "can_manage_security",
        "can_manage_settings",
    ]
    if request.POST.get("apply_preset") == "1":
        access.apply_role_preset(role)
    else:
        access.role = role
        for field in permission_fields:
            setattr(access, field, request.POST.get(field) == "1")
    access.updated_by = request.user
    access.save()
    messages.success(request, f"Owner Console permissions updated for {user.username}.")
    return redirect("owner:staff")


@owner_required
def reports(request):
    return render(request, "owner/reports.html", _owner_context(request))


@owner_required
def export_report(request, report_name):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="avan-{report_name}.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)

    if report_name == "orders":
        writer.writerow(["number", "created_at", "status", "customer", "phone", "total_toman"])
        for order in Order.objects.order_by("-created_at").iterator():
            writer.writerow([order.number, order.created_at.isoformat(), order.status, order.customer_name, order.phone, order.total_amount])
    elif report_name == "inventory":
        writer.writerow(["sku", "product", "color", "size", "stock", "active"])
        for variant in ProductVariant.objects.select_related("product", "color", "size").order_by("product__name").iterator():
            writer.writerow([variant.sku, variant.product.name, variant.color.name, variant.size.name, variant.stock, variant.is_active])
    elif report_name == "customers":
        writer.writerow(["username", "display_name", "email", "active", "joined_at"])
        for user in User.objects.order_by("-date_joined").iterator():
            writer.writerow([user.username, user.display_name, user.email, user.is_active, user.date_joined.isoformat()])
    elif report_name == "products":
        writer.writerow(["id", "name", "slug", "category", "base_price", "type", "active", "featured"])
        for product in Product.objects.select_related("category").order_by("name").iterator():
            writer.writerow([product.id, product.name, product.slug, product.category.name, product.base_price, product.product_type, product.is_active, product.is_featured])
    else:
        response.status_code = 404
        response.write("Unknown report")
    return response


@owner_required
def settings_view(request):
    owner_settings = OwnerSettings.load()
    marketplace_settings = MarketplaceSettings.load()
    owner_form = OwnerSettingsForm(request.POST or None, instance=owner_settings, prefix="owner")
    marketplace_form = MarketplaceSettingsForm(request.POST or None, instance=marketplace_settings, prefix="marketplace")

    if request.method == "POST":
        section = request.POST.get("section")
        if section == "owner" and owner_form.is_valid():
            owner_form.save()
            messages.success(request, "Owner settings saved.")
            return redirect("owner:settings")
        if section == "marketplace" and marketplace_form.is_valid():
            marketplace_form.save()
            messages.success(request, "Marketplace settings saved.")
            return redirect("owner:settings")

    return render(
        request,
        "owner/settings.html",
        _owner_context(
            request,
            owner_form=owner_form,
            marketplace_form=marketplace_form,
            marketplace_settings=marketplace_settings,
        ),
    )
