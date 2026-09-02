from django.urls import path
from .views import PaymentAttemptDetailAPIView, DevPaymentSuccessAPIView

urlpatterns = [
    path("<uuid:payment_id>/", PaymentAttemptDetailAPIView.as_view(), name="payment-detail"),
    path("<uuid:payment_id>/dev-success/", DevPaymentSuccessAPIView.as_view(), name="payment-dev-success"),
]
