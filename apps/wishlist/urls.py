from django.urls import path
from .views import WishlistAPIView, WishlistItemAPIView

urlpatterns = [
    path("", WishlistAPIView.as_view(), name="wishlist"),
    path("<int:product_id>/", WishlistItemAPIView.as_view(), name="wishlist-item"),
]
