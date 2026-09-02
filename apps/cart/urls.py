from django.urls import path
from .views import CartCreateAPIView, CartDetailAPIView, CartItemCreateAPIView, CartItemDetailAPIView, CartCouponAPIView

urlpatterns = [
    path("", CartCreateAPIView.as_view(), name="cart-create"),
    path("<uuid:token>/", CartDetailAPIView.as_view(), name="cart-detail"),
    path("<uuid:token>/items/", CartItemCreateAPIView.as_view(), name="cart-item-create"),
    path("<uuid:token>/items/<int:item_id>/", CartItemDetailAPIView.as_view(), name="cart-item-detail"),
    path("<uuid:token>/coupon/", CartCouponAPIView.as_view(), name="cart-coupon"),
]
