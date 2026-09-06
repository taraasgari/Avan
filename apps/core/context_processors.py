import os


def _appearance_context():
    defaults = {
        "primary_color": os.environ.get("AVAN_PRIMARY_COLOR", "#D50000"),
        "light_background": "#FFFFFF",
        "light_surface": "#F7F7F7",
        "dark_background": "#0D0D0F",
        "dark_surface": "#17171A",
        "base_font_size": 17,
        "persian_font_size": 18,
        "content_width": 1440,
        "page_gutter": 32,
        "header_height": 76,
        "section_spacing": 72,
        "card_radius": 12,
        "button_radius": 8,
        "card_shadow": True,
    }
    try:
        from apps.owner.models import SiteAppearance

        appearance = SiteAppearance.load()
        return {
            "primary_color": appearance.primary_color,
            "light_background": appearance.light_background,
            "light_surface": appearance.light_surface,
            "dark_background": appearance.dark_background,
            "dark_surface": appearance.dark_surface,
            "base_font_size": appearance.base_font_size,
            "persian_font_size": appearance.persian_font_size,
            "content_width": appearance.content_width,
            "page_gutter": appearance.page_gutter,
            "header_height": appearance.header_height,
            "section_spacing": appearance.section_spacing,
            "card_radius": appearance.card_radius,
            "button_radius": appearance.button_radius,
            "card_shadow": appearance.card_shadow,
        }
    except Exception:
        # Migrations, first boot, database outages and management commands should not
        # fail just because visual settings cannot be read yet.
        return defaults


def brand(request):
    unread_notifications = 0
    if getattr(request, "user", None) is not None and request.user.is_authenticated:
        try:
            from apps.growth.notifications import allowed_notification_kinds
            kinds = allowed_notification_kinds(request.user)
            unread_notifications = request.user.notifications.filter(is_read=False, kind__in=kinds).count() if kinds else 0
        except Exception:
            unread_notifications = request.user.notifications.filter(is_read=False).count()

    appearance = _appearance_context()
    return {
        "AVAN_BRAND_NAME": os.environ.get("AVAN_BRAND_NAME", "AVAN"),
        "AVAN_PRIMARY_COLOR": appearance["primary_color"],
        "AVAN_APPEARANCE": appearance,
        "AVAN_UNREAD_NOTIFICATIONS": unread_notifications,
    }
