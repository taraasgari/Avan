from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("shop/", include("apps.catalog.web_urls")),
    path("api/catalog/", include("apps.catalog.urls")),
    path("api/cart/", include("apps.cart.urls")),
    path("api/", include("apps.orders.urls")),
    path("api/payments/", include("apps.payments.urls")),
    path("api/wishlist/", include("apps.wishlist.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("bag/", include("apps.cart.web_urls")),
    path("", include("apps.orders.web_urls")),
    path(
    "account/",
    include("apps.accounts.urls"),
),
    path("", include("apps.designs.web_urls")),
    path("api/designs/", include("apps.designs.urls")),
    path("", include("apps.experience.urls")),
    path("", include("apps.wardrobe.urls")),
    path("", include("apps.core.search_urls")),
    path("", include("apps.marketplace.urls")),
    path("owner/", include("apps.owner.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
