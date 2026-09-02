from django.urls import path

from . import views


app_name = "owner"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("products/", views.products, name="products"),
    path("products/new/", views.product_edit, name="product-new"),
    path("products/<int:product_id>/", views.product_edit, name="product-edit"),
    path("warehouse/", views.warehouse, name="warehouse"),
    path("orders/", views.orders, name="orders"),
    path("orders/<int:order_id>/", views.order_detail, name="order-detail"),
    path("customers/", views.customers, name="customers"),
    path("customers/<int:user_id>/", views.customer_detail, name="customer-detail"),
    path("customers/<int:user_id>/toggle-active/", views.customer_toggle_active, name="customer-toggle-active"),
    path("designs/", views.designs, name="designs"),
    path("designs/<uuid:design_id>/moderate/", views.design_moderate, name="design-moderate"),
    path("creators/", views.creators, name="creators"),
    path("marketing/", views.marketing, name="marketing"),
    path("finance/", views.finance, name="finance"),
    path("finance/payout/<uuid:payout_id>/", views.payout_action, name="payout-action"),
    path("staff/", views.staff, name="staff"),
    path("staff/<int:user_id>/toggle/", views.staff_toggle, name="staff-toggle"),
    path("reports/", views.reports, name="reports"),
    path("data/", views.data_center, name="data-center"),
    path("reports/export/<str:report_name>/", views.export_report, name="export-report"),
    path("settings/", views.settings_view, name="settings"),
]
