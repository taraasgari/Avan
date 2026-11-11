from django.urls import path

from . import analytics_views, catalog_views, views


app_name = "owner"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("analytics/", analytics_views.analytics, name="analytics"),
    path("catalog/", catalog_views.catalog_manager, name="catalog-manager"),
    path("catalog/<str:entity>/<int:object_id>/delete/", catalog_views.catalog_delete, name="catalog-delete"),
    path("products/", views.products, name="products"),
    path("products/new/", views.product_edit, name="product-new"),
    path("products/<int:product_id>/", views.product_edit, name="product-edit"),
    path("products/<int:product_id>/studio/", views.product_studio, name="product-studio"),
    path("products/<int:product_id>/media/", catalog_views.product_media, name="product-media"),
    path("products/<int:product_id>/variants/", catalog_views.variant_manager, name="variant-manager"),
    path("shipping-methods/", catalog_views.shipping_methods, name="shipping-methods"),
    path("warehouse/", views.warehouse, name="warehouse"),
    path("orders/", views.orders, name="orders"),
    path("orders/<int:order_id>/", views.order_detail, name="order-detail"),
    path("customers/", views.customers, name="customers"),
    path("support/", views.support_tickets, name="support"),
    path("support/<uuid:reference>/", views.support_ticket_detail, name="support-detail"),
    path("customers/<int:user_id>/", views.customer_detail, name="customer-detail"),
    path("customers/<int:user_id>/toggle-active/", views.customer_toggle_active, name="customer-toggle-active"),
    path("designs/", views.designs, name="designs"),
    path("designs/<uuid:design_id>/moderate/", views.design_moderate, name="design-moderate"),
    path("creators/", views.creators, name="creators"),
    path("marketing/", views.marketing, name="marketing"),
    path("play/", views.play_manager, name="play-manager"),
    path("play/games/<int:game_id>/toggle/", views.game_visibility_toggle, name="game-visibility-toggle"),
    path("play/games/<int:game_id>/quick-update/", views.game_quick_update, name="game-quick-update"),
    path("play/challenges/<int:challenge_id>/toggle/", views.challenge_visibility_toggle, name="challenge-visibility-toggle"),
    path("play/challenges/<int:challenge_id>/quick-update/", views.challenge_quick_update, name="challenge-quick-update"),
    path("finance/", views.finance, name="finance"),
    path("finance/payout/<uuid:payout_id>/", views.payout_action, name="payout-action"),
    path("staff/", views.staff, name="staff"),
    path("staff/<int:user_id>/toggle/", views.staff_toggle, name="staff-toggle"),
    path("staff/<int:user_id>/permissions/", views.staff_access_update, name="staff-access-update"),
    path("reports/", views.reports, name="reports"),
    path("reports/export/<str:report_name>/", views.export_report, name="export-report"),
    path("settings/", views.settings_view, name="settings"),
    path("appearance/", views.appearance_editor, name="appearance"),
    path("design/upload/", views.page_design_upload, name="page-design-upload"),
    path("design/api/", views.page_design_api, name="page-design-api"),
    path("design/", views.page_designer, name="page-designer"),
]
