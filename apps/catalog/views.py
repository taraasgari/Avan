from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.shortcuts import render
from rest_framework import generics
from django.shortcuts import get_object_or_404, render

from .models import Category, Color, Product, ProductVariant, Size
from .serializers import ProductSerializer


class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return (
            Product.objects
            .filter(is_active=True)
            .select_related("category")
            .prefetch_related("variants__color", "variants__size")
        )


def shop(request):
    products = (
        Product.objects
        .filter(is_active=True)
        .select_related("category")
        .prefetch_related(
            "images",
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.filter(is_active=True)
                .select_related("color", "size"),
            ),
        )
    )

    category = request.GET.get("category", "").strip()
    color = request.GET.get("color", "").strip()
    size = request.GET.get("size", "").strip()
    product_type = request.GET.get("type", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    search = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "newest").strip()

    if category:
        products = products.filter(category__slug=category)

    if color:
        products = products.filter(
            variants__color__slug=color,
            variants__is_active=True,
            variants__stock__gt=0,
        )

    if size:
        products = products.filter(
            variants__size__name__iexact=size,
            variants__is_active=True,
            variants__stock__gt=0,
        )

    if product_type in {
        Product.ProductType.READY,
        Product.ProductType.CUSTOMIZABLE,
    }:
        products = products.filter(product_type=product_type)

    if min_price.isdigit():
        products = products.filter(base_price__gte=int(min_price))

    if max_price.isdigit():
        products = products.filter(base_price__lte=int(max_price))

    if search:
        products = products.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(category__name__icontains=search)
        )

    sort_map = {
        "newest": "-created_at",
        "oldest": "created_at",
        "price-low": "base_price",
        "price-high": "-base_price",
        "name": "name",
    }

    products = products.order_by(
        sort_map.get(sort, "-created_at")
    ).distinct()

    paginator = Paginator(products, 12)
    page = paginator.get_page(request.GET.get("page"))

    query_params = request.GET.copy()
    query_params.pop("page", None)

    context = {
        "page_obj": page,
        "categories": Category.objects.filter(is_active=True),
        "colors": Color.objects.all().order_by("name"),
        "sizes": Size.objects.all(),
        "selected": {
            "category": category,
            "color": color,
            "size": size,
            "type": product_type,
            "min_price": min_price,
            "max_price": max_price,
            "q": search,
            "sort": sort,
        },
        "query_string": query_params.urlencode(),
    }

    return render(request, "catalog/shop.html", context)

def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects
        .filter(is_active=True)
        .select_related("category")
        .prefetch_related(
            "images",
            "variants__color",
            "variants__size",
        ),
        slug=slug,
    )

    variants = [
        {
            "id": variant.id,
            "color_id": variant.color_id,
            "color": variant.color.name,
            "color_slug": variant.color.slug,
            "color_hex": variant.color.hex_code or "#dddddd",
            "size_id": variant.size_id,
            "size": variant.size.name,
            "price": int(variant.price),
            "stock": variant.available_stock,
        }
        for variant in product.variants.filter(is_active=True)
    ]

    colors = []
    color_ids = set()

    sizes = []
    size_ids = set()

    for variant in product.variants.filter(is_active=True):
        if variant.color_id not in color_ids:
            colors.append(variant.color)
            color_ids.add(variant.color_id)

        if variant.size_id not in size_ids:
            sizes.append(variant.size)
            size_ids.add(variant.size_id)

    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
            "variants_data": variants,
            "colors": colors,
            "sizes": sizes,
        },
    )