import os


def brand(request):
    unread_notifications = 0
    if getattr(request, "user", None) is not None and request.user.is_authenticated:
        try:
            from apps.growth.notifications import allowed_notification_kinds
            kinds = allowed_notification_kinds(request.user)
            unread_notifications = request.user.notifications.filter(is_read=False, kind__in=kinds).count() if kinds else 0
        except Exception:
            unread_notifications = request.user.notifications.filter(is_read=False).count()

    return {
        "AVAN_BRAND_NAME": os.environ.get("AVAN_BRAND_NAME", "AVAN"),
        "AVAN_PRIMARY_COLOR": os.environ.get("AVAN_PRIMARY_COLOR", "#D50000"),
        "AVAN_UNREAD_NOTIFICATIONS": unread_notifications,
    }
