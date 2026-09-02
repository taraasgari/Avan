from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render

from apps.catalog.models import ProductVariant
from apps.orders.models import Order
from apps.owner.decorators import owner_required

from .forms import AddressForm, ProductionBatchForm, ReturnRequestForm, ShipmentForm, SupplierForm
from .models import Address, InventoryMovement, ProductionBatch, ReturnRequest, Shipment, ShippingMethod, Supplier
from .services import adjust_stock, update_shipment


@login_required(login_url="/account/login/")
def address_book(request):
    edit_id = request.GET.get("edit")
    instance = get_object_or_404(Address, pk=edit_id, user=request.user) if edit_id else None
    form = AddressForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        address = form.save(commit=False)
        address.user = request.user
        address.save()
        if address.is_default:
            Address.objects.filter(user=request.user).exclude(pk=address.pk).update(is_default=False)
        elif not Address.objects.filter(user=request.user, is_default=True).exists():
            address.is_default = True
            address.save(update_fields=["is_default"])
        messages.success(request, "Address saved.")
        return redirect("operations:addresses")
    return render(request, "operations/address_book.html", {"addresses": Address.objects.filter(user=request.user), "form": form, "editing": instance})


@login_required(login_url="/account/login/")
def address_action(request, address_id, action):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    address = get_object_or_404(Address, pk=address_id, user=request.user)
    if action == "default":
        Address.objects.filter(user=request.user).update(is_default=False)
        address.is_default = True
        address.save(update_fields=["is_default"])
    elif action == "delete":
        was_default = address.is_default
        address.delete()
        if was_default:
            next_address = Address.objects.filter(user=request.user).first()
            if next_address:
                next_address.is_default = True
                next_address.save(update_fields=["is_default"])
    else:
        raise Http404
    return redirect("operations:addresses")


@login_required(login_url="/account/login/")
def returns(request):
    return render(request, "operations/returns.html", {"returns": ReturnRequest.objects.filter(user=request.user).select_related("order")})


@login_required(login_url="/account/login/")
def return_create(request, order_number):
    order = get_object_or_404(Order, number=order_number, user=request.user)
    if order.status != Order.Status.DELIVERED:
        messages.error(request, "Returns can be requested after delivery.")
        return redirect("operations:returns")
    if ReturnRequest.objects.filter(order=order, user=request.user).exclude(status__in=[ReturnRequest.Status.REJECTED, ReturnRequest.Status.CLOSED]).exists():
        messages.info(request, "An active return request already exists for this order.")
        return redirect("operations:returns")
    form = ReturnRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.order = order
        obj.user = request.user
        obj.save()
        messages.success(request, "Return request submitted.")
        return redirect("operations:returns")
    return render(request, "operations/return_create.html", {"order": order, "form": form})


@owner_required
def owner_operations(request):
    context = {
        "shipments_pending": Shipment.objects.exclude(status__in=[Shipment.Status.DELIVERED, Shipment.Status.RETURNED]).count(),
        "returns_open": ReturnRequest.objects.exclude(status__in=[ReturnRequest.Status.REJECTED, ReturnRequest.Status.REFUNDED, ReturnRequest.Status.CLOSED]).count(),
        "production_open": ProductionBatch.objects.exclude(status__in=[ProductionBatch.Status.RECEIVED, ProductionBatch.Status.CANCELLED]).count(),
        "inventory_delta": InventoryMovement.objects.aggregate(v=Sum("delta"))["v"] or 0,
        "recent_shipments": Shipment.objects.select_related("order", "method")[:8],
        "recent_returns": ReturnRequest.objects.select_related("order", "user")[:8],
    }
    return render(request, "owner/operations.html", context)


@owner_required
def owner_shipping(request):
    order_id = request.GET.get("order")
    shipment = None
    form = None
    if order_id:
        order = get_object_or_404(Order, pk=order_id)
        shipment, _ = Shipment.objects.get_or_create(order=order)
        form = ShipmentForm(request.POST or None, instance=shipment)
        if request.method == "POST" and form.is_valid():
            update_shipment(shipment=shipment, cleaned_data=form.cleaned_data)
            messages.success(request, "Shipment updated.")
            return redirect(f"/owner/shipping/?order={order.id}")
    return render(request, "owner/shipping.html", {
        "shipments": Shipment.objects.select_related("order", "method")[:100],
        "eligible_orders": Order.objects.filter(status__in=[Order.Status.PAID, Order.Status.PROCESSING, Order.Status.SHIPPED]).order_by("-created_at")[:100],
        "shipment": shipment,
        "form": form,
        "methods": ShippingMethod.objects.filter(is_active=True),
    })


@owner_required
def owner_returns(request):
    if request.method == "POST":
        item = get_object_or_404(ReturnRequest, pk=request.POST.get("return_id"))
        status = request.POST.get("status")
        allowed = {choice for choice, _ in ReturnRequest.Status.choices}
        if status not in allowed:
            return HttpResponseBadRequest("Invalid status")
        item.status = status
        item.owner_note = request.POST.get("owner_note", "")
        try:
            item.refund_amount = Decimal(request.POST.get("refund_amount") or "0")
        except Exception:
            return HttpResponseBadRequest("Invalid refund amount")
        item.save(update_fields=["status", "owner_note", "refund_amount", "updated_at"])
        messages.success(request, "Return request updated. No money is moved automatically by this action.")
        return redirect("operations:owner-returns")
    return render(request, "owner/returns.html", {"returns": ReturnRequest.objects.select_related("order", "user")[:200], "return_status_choices": ReturnRequest.Status.choices})


@owner_required
def owner_inventory(request):
    if request.method == "POST":
        allowed_kinds = {value for value, _ in InventoryMovement.Kind.choices}
        if request.POST.get("kind") not in allowed_kinds:
            messages.error(request, "Invalid inventory movement type.")
            return redirect("operations:owner-inventory")
        try:
            adjust_stock(
                variant_id=int(request.POST.get("variant_id")),
                delta=int(request.POST.get("delta")),
                kind=request.POST.get("kind"),
                actor=request.user,
                note=request.POST.get("note", ""),
            )
        except (ValueError, ValidationError, ProductVariant.DoesNotExist) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "Inventory updated and movement recorded.")
        return redirect("operations:owner-inventory")
    q = request.GET.get("q", "").strip()
    variants = ProductVariant.objects.select_related("product", "color", "size").filter(is_active=True)
    if q:
        variants = variants.filter(sku__icontains=q) | variants.filter(product__name__icontains=q)
    return render(request, "owner/inventory_movements.html", {"movements": InventoryMovement.objects.select_related("variant__product", "actor")[:200], "variants": variants[:100]})


@owner_required
def owner_production(request):
    supplier_form = SupplierForm(prefix="supplier")
    batch_form = ProductionBatchForm(prefix="batch")
    if request.method == "POST":
        kind = request.POST.get("form_kind")
        if kind == "supplier":
            supplier_form = SupplierForm(request.POST, prefix="supplier")
            if supplier_form.is_valid():
                supplier_form.save()
                messages.success(request, "Supplier saved.")
                return redirect("operations:owner-production")
        elif kind == "batch":
            batch_form = ProductionBatchForm(request.POST, prefix="batch")
            if batch_form.is_valid():
                batch_form.save()
                messages.success(request, "Production batch saved.")
                return redirect("operations:owner-production")
    return render(request, "owner/production.html", {"suppliers": Supplier.objects.all(), "batches": ProductionBatch.objects.select_related("product", "supplier")[:100], "supplier_form": supplier_form, "batch_form": batch_form})
