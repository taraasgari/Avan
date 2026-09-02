from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.shortcuts import render

from apps.catalog.models import Product


def home(request):
    featured_products = (
        Product.objects
        .filter(is_active=True)
        .select_related("category")
        .prefetch_related("images", "variants")
        .order_by("-is_featured", "-created_at")[:8]
    )

    return render(
        request,
        "core/home.html",
        {
            "featured_products": featured_products,
        },
    )


def health(request):
    return JsonResponse({
        "status": "ok",
        "service": "avan-web",
    })


def service_worker(request):
    response = FileResponse(
        open(settings.BASE_DIR / "static" / "pwa" / "sw.js", "rb"),
        content_type="application/javascript",
    )
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response