from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.models import Cart
from apps.operations.models import Address, ShippingMethod

from .models import Order
from .serializers import CheckoutSerializer, OrderSerializer
from .services import CheckoutError, place_order


class CheckoutAPIView(APIView):
    def post(self, request, cart_token):
        cart = get_object_or_404(Cart, token=cart_token)
        if cart.user_id and (not request.user.is_authenticated or request.user.id != cart.user_id):
            return Response({"detail": "Not found."}, status=404)

        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)

        address_id = data.pop("address_id", None)
        if address_id:
            if not request.user.is_authenticated:
                return Response({"detail": "Sign in to use a saved address."}, status=400)
            saved = get_object_or_404(Address, pk=address_id, user=request.user)
            data.update(
                {
                    "customer_name": saved.recipient_name,
                    "phone": saved.phone,
                    "email": data.get("email") or request.user.email or "",
                    "province": saved.province,
                    "city": saved.city,
                    "address": saved.address,
                    "postal_code": saved.postal_code,
                }
            )

        shipping_method_id = data.pop("shipping_method_id", None)
        shipping_method = None
        if shipping_method_id:
            shipping_method = get_object_or_404(ShippingMethod, pk=shipping_method_id, is_active=True)
        data["_shipping_method"] = shipping_method

        try:
            order, created = place_order(
                cart=cart,
                checkout_data=data,
                idempotency_key=data.get("idempotency_key"),
                user=request.user,
            )
        except CheckoutError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class OrderDetailAPIView(APIView):
    def get(self, request, number):
        order = get_object_or_404(
            Order.objects.prefetch_related("items", "reservations", "payment_attempts").select_related("user"),
            number=number,
        )
        if order.user_id and (not request.user.is_authenticated or request.user.id != order.user_id):
            return Response({"detail": "Not found."}, status=404)
        return Response(OrderSerializer(order).data)
