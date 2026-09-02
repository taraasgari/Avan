from django.urls import path

from . import search_views

app_name = "core_search"

urlpatterns = [
    path("search/", search_views.search, name="search"),
]
