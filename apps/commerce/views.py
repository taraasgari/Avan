from decimal import Decimal

from django.contrib import messages
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.operations.models import ShippingMethod
from apps.orders.models import Order
from apps.owner.decorators import owner_required

from .forms import CampaignForm, CommerceSettingsForm, ShippingRuleForm
from .models import AbandonedCartEvent, Campaign, CommerceSettings, Refund, ShippingRule
from .services import approve_refund, complete_refund, create_refund, detect_abandoned_carts, shipping_quote


class ShippingQuoteAPIView(APIView):
    def post(self, request):
        method = get_object_or_404(ShippingMethod, pk=request.data.get("shipping_method_id"), is_active=True)
        try:
            subtotal = Decimal(str(request.data.get("subtotal") or 0))
        except Exception:
            return Response({"detail": "Invalid subtotal."}, status=400)
        price, source = shipping_quote(
            method=method,
            subtotal=subtotal,
            province=request.data.get("province", ""),
            city=request.data.get("city", ""),
        )
        return Response({"shipping_amount": str(price), "source": source})


@owner_required
def owner_commerce(request):
    config = CommerceSettings.load()
    if request.method == "POST" and request.POST.get("form_kind") == "settings":
        form = CommerceSettingsForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Commerce settings saved.")
            return redirect("commerce:owner-commerce")
    else:
        form = CommerceSettingsForm(instance=config)
    return render(request, "owner/commerce.html", {
        "form": form,
        "rules_count": ShippingRule.objects.count(),
        "campaigns_active": Campaign.objects.filter(is_active=True).count(),
        "refunds_open": Refund.objects.exclude(status__in=[Refund.Status.SUCCEEDED, Refund.Status.CANCELLED]).count(),
        "abandoned_open": AbandonedCartEvent.objects.filter(status=AbandonedCartEvent.Status.DETECTED).count(),
        "refunded_total": Refund.objects.filter(status=Refund.Status.SUCCEEDED).aggregate(v=Sum("amount"))["v"] or 0,
    })


@owner_required
def owner_shipping_rules(request):
    form = ShippingRuleForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Shipping rule saved.")
        return redirect("commerce:owner-shipping-rules")
    return render(request, "owner/shipping_rules.html", {"form": form, "rules": ShippingRule.objects.select_related("method")[:200]})


@owner_required
@require_POST
def owner_shipping_rule_delete(request, rule_id):
    get_object_or_404(ShippingRule, pk=rule_id).delete()
    messages.success(request, "Shipping rule deleted.")
    return redirect("commerce:owner-shipping-rules")


@owner_required
def owner_campaigns(request):
    form = CampaignForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Campaign saved.")
        return redirect("commerce:owner-campaigns")
    return render(request, "owner/campaigns.html", {"form": form, "campaigns": Campaign.objects.select_related("coupon")[:200]})


@owner_required
def owner_abandoned(request):
    if request.method == "POST" and request.POST.get("action") == "scan":
        result = detect_abandoned_carts()
        messages.success(request, f"Scan complete: {result['created']} detected, {result['recovered']} recovered.")
        return redirect("commerce:owner-abandoned")
    return render(request, "owner/abandoned_carts.html", {"events": AbandonedCartEvent.objects.select_related("cart__user")[:250]})


@owner_required
def owner_refunds(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            order = get_object_or_404(Order, pk=request.POST.get("order_id"))
            try:
                create_refund(order=order, amount=request.POST.get("amount"), actor=request.user, reason=request.POST.get("reason", ""))
            except ValueError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, "Refund request created.")
        else:
            refund = get_object_or_404(Refund, pk=request.POST.get("refund_id"))
            if action == "approve":
                approve_refund(refund=refund, actor=request.user)
                messages.success(request, "Refund approved. No money has been moved yet.")
            elif action == "mark-succeeded":
                complete_refund(refund=refund, actor=request.user, external_reference=request.POST.get("external_reference", "MANUAL"))
                messages.success(request, "Refund marked successful.")
            elif action == "cancel":
                refund.status = Refund.Status.CANCELLED
                refund.save(update_fields=["status", "updated_at"])
                messages.success(request, "Refund cancelled.")
        return redirect("commerce:owner-refunds")
    return render(request, "owner/refunds.html", {
        "refunds": Refund.objects.select_related("order", "requested_by", "approved_by")[:250],
        "orders": Order.objects.filter(status__in=[Order.Status.PAID, Order.Status.PROCESSING, Order.Status.SHIPPED, Order.Status.DELIVERED]).order_by("-created_at")[:100],
    })
