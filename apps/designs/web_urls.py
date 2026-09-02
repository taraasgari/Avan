from django.urls import path

from . import web_views

app_name = "designs_web"

urlpatterns = [
    path("design/", web_views.studio, name="studio"),
    path("design/<uuid:design_id>/", web_views.studio, name="studio-edit"),
    path("account/designs/", web_views.my_designs, name="my-designs"),
    path("account/saved-designs/", web_views.saved_designs, name="saved-designs"),
    path("explore/", web_views.explore, name="explore"),
    path("explore/<uuid:design_id>/", web_views.public_design, name="public-design"),
    path("creator/<str:username>/", web_views.creator_profile, name="creator-profile"),
    path(
        "creator/<str:username>/follow/",
        web_views.creator_follow_toggle,
        name="creator-follow",
    ),
]
