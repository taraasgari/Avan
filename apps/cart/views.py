from copy import deepcopy

from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import ProductVariant
from apps.coupons.models import Coupon
from apps.coupons.services import validate_coupon
from apps.designs.models import Design
from .models import Cart, CartItem
from .serializers import CartSerializer
from .services import available_stock


def _cart_for_request(request, token):
    cart = get_object_or_404(Cart, token=token, status=Cart.Status.OPEN)
    if cart.user_id and (not request.user.is_authenticated or request.user.id != cart.user_id):
        raise Http404
    return cart


def _snapshot_design(design):
    return {
        "id": str(design.id),
        "title": design.title,
        "owner_id": design.owner_id,
        "owner_name": design.owner.display_name or design.owner.username,
        "base_product_id": design.base_product_id,
        "base_color_id": design.base_color_id,
        "parent_design_id": str(design.parent_design_id) if design.parent_design_id else None,
        "design_data": deepcopy(design.design_data),
        "sale_price": int(design.sale_price or 0),
    }


def _allowed_design(request, design_id):
    if not design_id:
        return None
    design = get_object_or_404(
        Design.objects.select_related("owner", "base_product", "base_color"),
        id=design_id,
    )
    if request.user.is_authenticated and design.owner_id == request.user.id:
        return design
    if (
        design.status == Design.Status.PUBLISHED
        and design.visibility == Design.Visibility.PUBLIC
        and design.is_for_sale
    ):
        return design
    raise Http404


class CartCreateAPIView(APIView):
    def post(self, request):
        user = request.user if request.user.is_authenticated else None
        cart = Cart.objects.create(user=user)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


class CartDetailAPIView(APIView):
    def get_cart(self, token):
        return _cart_for_request(self.request, token)

    def get(self, request, token):
        return Response(CartSerializer(self.get_cart(token)).data)


class CartItemCreateAPIView(APIView):
    def post(self, request, token):
        cart = _cart_for_request(request, token)
        variant = get_object_or_404(
            ProductVariant.objects.select_related("product", "color", "size"),
            pk=request.data.get("variant_id"),
            is_active=True,
            product__is_active=True,
        )
        design = _allowed_design(request, request.data.get("design_id"))
        design_fee = 0
        if design and not (request.user.is_authenticated and design.owner_id == request.user.id):
            design_fee = design.sale_price if design.is_for_sale else 0

        if design:
            if design.base_product_id != variant.product_id:
                return Response({"detail": "This design belongs to another garment."}, status=409)
            if design.base_color_id and design.base_color_id != variant.color_id:
                return Response({"detail": "Choose the design's garment color."}, status=409)

        try:
            quantity = int(request.data.get("quantity", 1))
        except (TypeError, ValueError):
            return Response({"detail": "Invalid quantity."}, status=400)
        if quantity < 1:
            return Response({"detail": "Quantity must be at least 1."}, status=400)

        item = CartItem.objects.filter(cart=cart, variant=variant, design=design).first()
        new_quantity = quantity + (item.quantity if item else 0)
        if new_quantity > available_stock(variant):
            return Response({"detail": "Requested quantity is not available."}, status=409)

        created = item is None
        snapshot = _snapshot_design(design) if design else {}
        if created:
            item = CartItem.objects.create(
                cart=cart,
                variant=variant,
                design=design,
                design_snapshot=snapshot,
                design_fee=design_fee,
                quantity=new_quantity,
            )
        else:
            item.quantity = new_quantity
            if design:
                item.design_snapshot = snapshot
            item.save(update_fields=["quantity", "design_snapshot", "updated_at"])

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CartItemDetailAPIView(APIView):
    def patch(self, request, token, item_id):
        cart = _cart_for_request(request, token)
        item = get_object_or_404(CartItem.objects.select_related("variant"), cart=cart, pk=item_id)
        try:
            quantity = int(request.data.get("quantity"))
        except (TypeError, ValueError):
            return Response({"detail": "Invalid quantity."}, status=400)
        if quantity < 1:
            return Response({"detail": "Quantity must be at least 1."}, status=400)
        if quantity > available_stock(item.variant):
            return Response({"detail": "Requested quantity is not available."}, status=409)
        item.quantity = quantity
        item.save(update_fields=["quantity", "updated_at"])
        return Response(CartSerializer(cart).data)

    def delete(self, request, token, item_id):
        cart = _cart_for_request(request, token)
        item = get_object_or_404(CartItem, cart=cart, pk=item_id)
        item.delete()
        return Response(CartSerializer(cart).data)


class CartCouponAPIView(APIView):
    def post(self, request, token):
        cart = _cart_for_request(request, token)
        code = str(request.data.get("code", "")).strip().upper()
        coupon = get_object_or_404(Coupon, code__iexact=code)
        valid, message = validate_coupon(coupon, user=cart.user)
        if not valid:
            return Response({"detail": message}, status=400)
        cart.coupon = coupon
        cart.save(update_fields=["coupon", "updated_at"])
        return Response(CartSerializer(cart).data)

    def delete(self, request, token):
        cart = _cart_for_request(request, token)
        cart.coupon = None
        cart.save(update_fields=["coupon", "updated_at"])
        return Response(CartSerializer(cart).data)
