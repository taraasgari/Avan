from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.models import Cart
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
        data = serializer.validated_data
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
        order = get_object_or_404(Order.objects.prefetch_related("items", "reservations"), number=number)
        if order.user_id and (not request.user.is_authenticated or request.user.id != order.user_id):
            return Response({"detail": "Not found."}, status=404)
        return Response(OrderSerializer(order).data)
