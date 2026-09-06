from django.urls import path

from . import views

app_name = "experience"

urlpatterns = [
    path("drops/", views.drops, name="drops"),
    path("drops/<slug:slug>/", views.drop_detail, name="drop-detail"),
    path("challenges/", views.challenges, name="challenges"),
    path("challenges/<slug:slug>/", views.challenge_detail, name="challenge-detail"),
    path("play/", views.play_hub, name="play"),
    path("play/<slug:slug>/", views.game_detail, name="game-detail"),
    path("play/api/<slug:slug>/start/", views.game_start, name="game-start"),
    path("play/api/<slug:slug>/submit/", views.game_submit, name="game-submit"),
    path("rewards/", views.rewards, name="rewards"),
]
