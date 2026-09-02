from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("wishlist/", views.wishlist_page, name="wishlist"),
    path("profile/", views.profile_settings, name="profile-settings"),
    path("notifications/", views.notification_center, name="notifications"),
    path(
        "notifications/read-all/",
        views.notifications_mark_all_read,
        name="notifications-read-all",
    ),
    path(
        "notifications/<int:notification_id>/read/",
        views.notification_mark_read,
        name="notification-read",
    ),
]
