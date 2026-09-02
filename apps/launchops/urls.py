from django.urls import path

from . import views

app_name = "launchops"

urlpatterns = [
    path("_health/live/", views.live, name="live"),
    path("_health/ready/", views.ready, name="ready"),
    path("_metrics/", views.metrics, name="metrics"),
    path("owner/launch/", views.launch_dashboard, name="owner-launch"),
    path("owner/launch/audit/", views.audit_log, name="owner-audit"),
]
