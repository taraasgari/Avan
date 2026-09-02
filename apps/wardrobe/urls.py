from django.urls import path

from . import views

app_name = "wardrobe"

urlpatterns = [
    path("size-passport/", views.size_passport, name="size-passport"),
    path("outfits/", views.outfits, name="outfits"),
    path("outfits/create/", views.outfit_create, name="outfit-create"),
    path("outfits/<uuid:outfit_id>/", views.outfit_builder, name="outfit-builder"),
    path("outfits/<uuid:outfit_id>/update/", views.outfit_update, name="outfit-update"),
    path("outfits/<uuid:outfit_id>/delete/", views.outfit_delete, name="outfit-delete"),
    path("api/outfits/<uuid:outfit_id>/items/", views.outfit_add_item, name="outfit-add-item"),
    path(
        "api/outfits/<uuid:outfit_id>/items/<int:item_id>/",
        views.outfit_remove_item,
        name="outfit-remove-item",
    ),
]
