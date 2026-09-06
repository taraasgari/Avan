from django.urls import path
from . import creator_views, studio_owner_views, web_views

app_name = "designs_web"
urlpatterns = [
    path("design/garments/", web_views.garment_chooser, name="garment-chooser"),
    path("design/", web_views.studio, name="studio"),
    path("design/<uuid:design_id>/", web_views.studio, name="studio-edit"),
    path("design/studio-owner/settings/", studio_owner_views.owner_settings, name="studio-owner-settings"),
    path("design/studio-owner/fabric/", studio_owner_views.owner_fabric, name="studio-owner-fabric"),
    path("design/studio-owner/font/", studio_owner_views.owner_font, name="studio-owner-font"),
    path("design/studio-owner/sticker-category/", studio_owner_views.owner_sticker_category, name="studio-owner-sticker-category"),
    path("design/studio-owner/sticker/", studio_owner_views.owner_sticker, name="studio-owner-sticker"),
    path("design/studio-owner/garment/", studio_owner_views.owner_garment_profile, name="studio-owner-garment"),
    path("account/designs/", web_views.my_designs, name="my-designs"),
    path("account/saved-designs/", web_views.saved_designs, name="saved-designs"),
    path("account/creator/analytics/", creator_views.creator_analytics, name="creator-analytics"),
    path("explore/", web_views.explore, name="explore"),
    path("following/", creator_views.following_feed, name="following-feed"),
    path("explore/<uuid:design_id>/", web_views.public_design, name="public-design"),
    path("creator/<str:username>/", web_views.creator_profile, name="creator-profile"),
    path("creator/<str:username>/follow/", web_views.creator_follow_toggle, name="creator-follow"),
]
