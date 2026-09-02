from django.urls import path
from .views import CheckoutAPIView, OrderDetailAPIView

urlpatterns = [
    path("checkout/<uuid:cart_token>/", CheckoutAPIView.as_view(), name="checkout"),
    path("orders/<uuid:number>/", OrderDetailAPIView.as_view(), name="order-detail"),
]
