from django.urls import path

from . import views

app_name = "commerce"

urlpatterns = [
    path("api/commerce/shipping-quote/", views.ShippingQuoteAPIView.as_view(), name="shipping-quote"),
    path("owner/commerce/", views.owner_commerce, name="owner-commerce"),
    path("owner/commerce/shipping-rules/", views.owner_shipping_rules, name="owner-shipping-rules"),
    path("owner/commerce/shipping-rules/<int:rule_id>/delete/", views.owner_shipping_rule_delete, name="owner-shipping-rule-delete"),
    path("owner/commerce/campaigns/", views.owner_campaigns, name="owner-campaigns"),
    path("owner/commerce/abandoned-carts/", views.owner_abandoned, name="owner-abandoned"),
    path("owner/commerce/refunds/", views.owner_refunds, name="owner-refunds"),
]
