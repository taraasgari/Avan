from django.urls import path

from . import views

app_name = "catalog_web"

urlpatterns = [
    path("", views.shop, name="shop"),
    path("<slug:slug>/", views.product_detail, name="product-detail"),
]