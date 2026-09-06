from django.urls import path
from . import search_views

app_name = "core_search"

urlpatterns = [
    path("search/suggest/", search_views.search_suggest, name="search-suggest"),
    path("search/", search_views.search, name="search"),
]
