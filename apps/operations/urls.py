from django.urls import path

from . import views

app_name = "operations"

urlpatterns = [
    path("account/addresses/", views.address_book, name="addresses"),
    path("account/addresses/<int:address_id>/<str:action>/", views.address_action, name="address-action"),
    path("account/returns/", views.returns, name="returns"),
    path("account/returns/new/<uuid:order_number>/", views.return_create, name="return-create"),
    path("owner/operations/", views.owner_operations, name="owner-operations"),
    path("owner/shipping/", views.owner_shipping, name="owner-shipping"),
    path("owner/returns/", views.owner_returns, name="owner-returns"),
    path("owner/inventory-movements/", views.owner_inventory, name="owner-inventory"),
    path("owner/production/", views.owner_production, name="owner-production"),
]
