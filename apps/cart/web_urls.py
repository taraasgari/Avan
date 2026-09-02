from django.urls import path

from .web_views import bag

app_name = "cart_web"

urlpatterns = [
    path("", bag, name="bag"),
]