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



def _page_design_context(request):
    defaults = {
        "page_key": "", "background": "", "text_color": "", "surface": "",
        "accent": "", "section_gap": "", "card_radius": "", "hide_header": False,
        "hero_kicker_fa": "", "hero_kicker_en": "", "hero_title_fa": "", "hero_title_en": "",
        "hero_subtitle_fa": "", "hero_subtitle_en": "", "primary_label_fa": "",
        "primary_label_en": "", "primary_url": "", "secondary_label_fa": "",
        "secondary_label_en": "", "secondary_url": "",
    }
    try:
        from apps.owner.models import PageDesign
        path = getattr(request, "path", "/") or "/"
        key = "home" if path == "/" else None
        mapping = [
            ("/shop/", "product" if path != "/shop/" else "shop"),
            ("/design/garments/", "design"), ("/design/", "studio"),
            ("/collections/", "collections"), ("/explore/", "explore"),
            ("/play/", "play"), ("/challenges/", "challenges"), ("/drops/", "drops"),
            ("/account/support/", "support"), ("/account/", "account"),
        ]
        if key is None:
            for prefix, candidate in mapping:
                if path.startswith(prefix):
                    key = candidate
                    break
        if not key:
            return defaults
        obj = PageDesign.objects.filter(page_key=key).first()
        if not obj:
            return defaults
        use_draft = (
            request.GET.get("visual_preview") == "1"
            and getattr(request, "user", None) is not None
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.is_staff)
        )
        data = dict(obj.draft_data if use_draft else obj.published_data or {})
        defaults.update(data)
        defaults["page_key"] = key
        defaults["is_preview"] = use_draft
        return defaults
    except Exception:
        return defaults


def brand(request):
    unread_notifications = 0
    support_unread = 0
    if getattr(request, "user", None) is not None and request.user.is_authenticated:
        try:
            from apps.growth.notifications import allowed_notification_kinds
            kinds = allowed_notification_kinds(request.user)
            unread_notifications = request.user.notifications.filter(is_read=False, kind__in=kinds).count() if kinds else 0
        except Exception:
            unread_notifications = request.user.notifications.filter(is_read=False).count()
        try:
            from apps.accounts.models import SupportTicket
            support_unread = request.user.support_tickets.filter(status=SupportTicket.Status.WAITING_USER).count()
        except Exception:
            support_unread = 0

    appearance = _appearance_context()
    page_design = _page_design_context(request)
    return {
        "AVAN_BRAND_NAME": os.environ.get("AVAN_BRAND_NAME", "AVAN"),
        "AVAN_PRIMARY_COLOR": appearance["primary_color"],
        "AVAN_APPEARANCE": appearance,
        "AVAN_UNREAD_NOTIFICATIONS": unread_notifications,
        "AVAN_SUPPORT_UNREAD": support_unread,
        "AVAN_PAGE_DESIGN": page_design,
    }
