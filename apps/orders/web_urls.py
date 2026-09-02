from django.urls import path

from .web_views import checkout_page, order_page


app_name = "orders_web"


urlpatterns = [
    path("checkout/", checkout_page, name="checkout"),
    path(
        "orders/<uuid:number>/",
        order_page,
        name="order-detail",
    ),
]