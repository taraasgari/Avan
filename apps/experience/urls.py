from django.urls import path

from . import views

app_name = "experience"

urlpatterns = [
    path("drops/", views.drops, name="drops"),
    path("drops/<slug:slug>/", views.drop_detail, name="drop-detail"),
    path("challenges/", views.challenges, name="challenges"),
    path("challenges/<slug:slug>/", views.challenge_detail, name="challenge-detail"),
    path("rewards/", views.rewards, name="rewards"),
]
