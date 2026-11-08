from django.urls import path

from . import web_views


app_name = "orders_web"

urlpatterns = [
    path("track/", web_views.track_order_page, name="track-order"),
    path("checkout/", web_views.checkout_page, name="checkout"),
    path("orders/<uuid:number>/", web_views.order_detail_page, name="order-detail"),
]
