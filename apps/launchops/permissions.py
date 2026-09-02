from .models import StaffAccess


# Most-specific prefixes must come first.
_OWNER_PATH_PERMISSIONS = [
    ("/owner/launch/", None),  # superuser only
    ("/owner/staff/", None),  # superuser only
    ("/owner/security/", "can_manage_security"),
    ("/owner/moderation/", "can_manage_designs"),
    ("/owner/growth/", "can_manage_marketing"),
    ("/owner/commerce/refunds/", "can_manage_finance"),
    ("/owner/commerce/campaigns/", "can_manage_marketing"),
    ("/owner/commerce/abandoned-carts/", "can_manage_marketing"),
    ("/owner/commerce/shipping-rules/", "can_manage_orders"),
    ("/owner/commerce/", ("can_manage_orders", "can_manage_finance", "can_manage_marketing")),
    ("/owner/content/", "can_manage_content"),
    ("/owner/analytics/", "can_view_analytics"),
    ("/owner/catalog/", "can_manage_catalog"),
    ("/owner/products/", "can_manage_catalog"),
    ("/owner/warehouse/", "can_manage_inventory"),
    ("/owner/inventory-movements/", "can_manage_inventory"),
    ("/owner/production/", "can_manage_inventory"),
    ("/owner/shipping-methods/", "can_manage_orders"),
    ("/owner/shipping/", "can_manage_orders"),
    ("/owner/returns/", "can_manage_orders"),
    ("/owner/operations/", ("can_manage_orders", "can_manage_inventory")),
    ("/owner/orders/", "can_manage_orders"),
    ("/owner/customers/", "can_manage_customers"),
    ("/owner/designs/", "can_manage_designs"),
    ("/owner/creators/", "can_manage_designs"),
    ("/owner/marketing/", "can_manage_marketing"),
    ("/owner/finance/", "can_manage_finance"),
    ("/owner/reports/", "can_manage_reports"),
    ("/owner/settings/", "can_manage_settings"),
    ("/owner/", "can_view_dashboard"),
]


def get_staff_access(user):
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_staff", False):
        return None
    try:
        return user.avan_staff_access
    except StaffAccess.DoesNotExist:
        return None


def permission_for_owner_path(path):
    for prefix, permission in _OWNER_PATH_PERMISSIONS:
        if path.startswith(prefix):
            return permission
    return None


def staff_can_access_path(user, path):
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    if not getattr(user, "is_staff", False):
        return False

    permission = permission_for_owner_path(path)
    # Unknown Owner Console routes and explicitly protected routes fail closed.
    if permission is None:
        return False

    access = get_staff_access(user)
    if not access:
        return False
    if isinstance(permission, (tuple, list, set)):
        return any(bool(getattr(access, key, False)) for key in permission)
    return bool(getattr(access, permission, False))
