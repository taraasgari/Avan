from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.services import confirm_payment
from .models import PaymentAttempt
from .serializers import PaymentAttemptSerializer


class PaymentAttemptDetailAPIView(APIView):
    def get(self, request, payment_id):
        payment = get_object_or_404(PaymentAttempt.objects.select_related("order"), pk=payment_id)
        return Response(PaymentAttemptSerializer(payment).data)


class DevPaymentSuccessAPIView(APIView):
    """Development-only payment simulator. Never exposed when DEBUG=False."""

    def post(self, request, payment_id):
        if not settings.DEBUG:
            return Response({"detail": "Not found."}, status=404)
        payment = get_object_or_404(PaymentAttempt.objects.select_related("order"), pk=payment_id)
        order = confirm_payment(payment.order, payment, external_reference=f"DEV-{payment.id}")
        return Response({"order": str(order.number), "order_status": order.status, "payment_status": payment.status})
