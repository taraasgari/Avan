from django.urls import path

from . import views

app_name = "growth"

urlpatterns = [
    path("offline/", views.offline_page, name="offline"),
    path("account/notification-preferences/", views.notification_preferences, name="notification-preferences"),
    path("report/design/<uuid:design_id>/", views.report_design, name="report-design"),
    path("report/creator/<str:username>/", views.report_creator, name="report-creator"),
    path("owner/growth/", views.growth_dashboard, name="owner-growth"),
    path("owner/growth/redirects/", views.seo_redirects, name="owner-seo-redirects"),
    path("owner/growth/redirects/<int:redirect_id>/delete/", views.seo_redirect_delete, name="owner-seo-redirect-delete"),
    path("owner/moderation/", views.moderation_queue, name="owner-moderation"),
    path("owner/moderation/<int:report_id>/", views.moderation_update, name="owner-moderation-update"),
    path("owner/security/", views.security_center, name="owner-security"),
]
