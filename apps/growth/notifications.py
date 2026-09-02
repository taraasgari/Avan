from .models import NotificationPreference


def allowed_notification_kinds(user):
    if not getattr(user, "is_authenticated", False):
        return []
    preference, _ = NotificationPreference.objects.get_or_create(user=user)
    kinds = []
    if preference.order_updates:
        kinds.append("order")
    if preference.social_activity:
        kinds.append("social")
    if preference.rewards:
        kinds.append("reward")
    if preference.product_and_drop_news or preference.security_alerts:
        kinds.append("system")
    return kinds
