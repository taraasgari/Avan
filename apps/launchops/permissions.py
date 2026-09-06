from .models import StaffAccess

# Most-specific paths first. None stays superuser-only.
_OWNER_PATH_SECTIONS = [
    ("/owner/launch/", None),
    ("/owner/staff/", None),
    ("/owner/security/", "security"),
    ("/owner/moderation/", "moderation"),
    ("/owner/growth/", "growth"),
    ("/owner/commerce/refunds/", "finance"),
    ("/owner/commerce/campaigns/", "marketing"),
    ("/owner/commerce/abandoned-carts/", "marketing"),
    ("/owner/commerce/shipping-rules/", "shipping"),
    ("/owner/commerce/", "commerce"),
    ("/owner/content/", "content"),
    ("/owner/appearance/", "appearance"),
    ("/owner/analytics/", "analytics"),
    ("/owner/catalog/", "catalog"),
    ("/owner/products/", "products"),
    ("/owner/warehouse/", "inventory"),
    ("/owner/inventory-movements/", "inventory"),
    ("/owner/production/", "production"),
    ("/owner/shipping-methods/", "shipping"),
    ("/owner/shipping/", "shipping"),
    ("/owner/returns/", "returns"),
    ("/owner/operations/", "operations"),
    ("/owner/orders/", "orders"),
    ("/owner/customers/", "customers"),
    ("/owner/support/", "support"),
    ("/owner/designs/", "designs"),
    ("/owner/creators/", "creators"),
    ("/owner/play/", "play"),
    ("/owner/marketing/", "marketing"),
    ("/owner/finance/", "finance"),
    ("/owner/reports/", "reports"),
    ("/owner/settings/", "settings"),
]


def get_staff_access(user):
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_staff", False):
        return None
    try:
        return user.avan_staff_access
    except StaffAccess.DoesNotExist:
        return None


def get_staff_sections(user):
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return set()
    if getattr(user, "is_superuser", False):
        return {key for key, _ in StaffAccess.SECTION_CHOICES} | {"staff", "launch"}
    access = get_staff_access(user)
    if not access:
        return set()
    if access.section_permissions:
        return set(access.section_permissions)
    # Legacy fallback for pre-Stage-19 records.
    sections = set()
    flags = {
        "dashboard": access.can_view_dashboard,
        "analytics": access.can_view_analytics,
        "products": access.can_manage_catalog,
        "catalog": access.can_manage_catalog,
        "inventory": access.can_manage_inventory,
        "production": access.can_manage_inventory,
        "orders": access.can_manage_orders,
        "operations": access.can_manage_orders,
        "shipping": access.can_manage_orders,
        "returns": access.can_manage_orders,
        "customers": access.can_manage_customers,
        "support": access.can_manage_customers,
        "designs": access.can_manage_designs,
        "creators": access.can_manage_designs,
        "moderation": access.can_manage_designs,
        "play": access.can_manage_marketing,
        "marketing": access.can_manage_marketing,
        "growth": access.can_manage_marketing,
        "finance": access.can_manage_finance,
        "commerce": access.can_manage_finance,
        "content": access.can_manage_content,
        "reports": access.can_manage_reports,
        "security": access.can_manage_security,
        "settings": access.can_manage_settings,
    }
    for key, enabled in flags.items():
        if enabled:
            sections.add(key)
    return sections


def section_for_owner_path(path):
    if path.rstrip("/") == "/owner":
        return "dashboard"
    for prefix, section in _OWNER_PATH_SECTIONS:
        if path.startswith(prefix):
            return section
    return None


def staff_can_access_path(user, path):
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    if not getattr(user, "is_staff", False):
        return False
    section = section_for_owner_path(path)
    if section is None:  # unknown route or explicitly owner-only route
        return False
    return section in get_staff_sections(user)
