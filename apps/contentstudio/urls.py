from django.urls import path

from . import views

app_name = "contentstudio"

urlpatterns = [
    path("collections/", views.collections_index, name="collections"),
    path("collections/<slug:slug>/", views.collection_detail, name="collection-detail"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap"),
    path("robots.txt", views.robots_txt, name="robots"),

    path("owner/content/", views.content_dashboard, name="owner-content"),
    path("owner/content/products/", views.product_content, name="owner-product-content"),
    path("owner/content/products/<int:product_id>/", views.product_content, name="owner-product-content-edit"),
    path("owner/content/categories/", views.category_content, name="owner-category-content"),
    path("owner/content/categories/<int:category_id>/", views.category_content, name="owner-category-content-edit"),
    path("owner/content/collections/", views.collections_manager, name="owner-collections"),
    path("owner/content/collections/<int:collection_id>/", views.collections_manager, name="owner-collection-edit"),
    path("owner/content/collections/<int:collection_id>/products/", views.collection_products, name="owner-collection-products"),
    path("owner/content/media/", views.media_library, name="owner-media"),
    path("owner/content/media/<int:asset_id>/delete/", views.media_delete, name="owner-media-delete"),
    path("owner/content/seo/", views.seo_manager, name="owner-seo"),
    path("owner/content/seo/<int:seo_id>/", views.seo_manager, name="owner-seo-edit"),
    path("owner/content/bulk/", views.bulk_catalog, name="owner-bulk"),
    path("owner/content/bulk/export/", views.export_catalog, name="owner-bulk-export"),
]
