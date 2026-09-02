import csv
from io import StringIO

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.catalog.models import Category, Product
from apps.owner.decorators import owner_required

from .forms import BulkCatalogForm, CategoryContentForm, CollectionForm, MediaAssetForm, ProductContentForm, SeoPageForm
from .models import CatalogImportJob, Collection, CollectionItem, MediaAsset, SeoPage
from .services import CSV_FIELDS, catalog_csv_rows, import_catalog_csv


def _owner_context(request, **extra):
    from apps.owner.views import _owner_context as owner_context
    return owner_context(request, **extra)


def _active_collections():
    now = timezone.now()
    return Collection.objects.filter(is_active=True).filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now)).filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))


def collections_index(request):
    collections = _active_collections().select_related("hero").annotate(product_count=Count("items"))
    return render(request, "contentstudio/collections.html", {"collections": collections})


def collection_detail(request, slug):
    collection = get_object_or_404(_active_collections().select_related("hero"), slug=slug)
    items = collection.items.select_related("product", "product__category").prefetch_related("product__images").filter(product__is_active=True)
    return render(request, "contentstudio/collection_detail.html", {"collection": collection, "items": items})


def sitemap_xml(request):
    base = request.build_absolute_uri("/").rstrip("/")
    urls = [{"loc": base + "/", "lastmod": None}, {"loc": base + "/shop/", "lastmod": None}, {"loc": base + "/collections/", "lastmod": None}]
    for product in Product.objects.filter(is_active=True).only("slug", "updated_at"):
        urls.append({"loc": f"{base}/shop/{product.slug}/", "lastmod": product.updated_at.date().isoformat()})
    for collection in _active_collections().only("slug", "updated_at"):
        urls.append({"loc": f"{base}/collections/{collection.slug}/", "lastmod": collection.updated_at.date().isoformat()})
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for item in urls:
        lines.append("<url>")
        lines.append(f"<loc>{item['loc']}</loc>")
        if item["lastmod"]:
            lines.append(f"<lastmod>{item['lastmod']}</lastmod>")
        lines.append("</url>")
    lines.append("</urlset>")
    return HttpResponse("\n".join(lines), content_type="application/xml; charset=utf-8")


def robots_txt(request):
    sitemap = request.build_absolute_uri("/sitemap.xml")
    body = f"User-agent: *\nAllow: /\nDisallow: /owner/\nDisallow: /admin/\nDisallow: /account/\nSitemap: {sitemap}\n"
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


@owner_required
def content_dashboard(request):
    return render(request, "owner/content.html", _owner_context(
        request,
        product_missing_en=Product.objects.filter(Q(name_en="") | Q(seo_title_en="")).count(),
        product_missing_fa=Product.objects.filter(Q(name_fa="") | Q(seo_title_fa="")).count(),
        category_missing_fa=Category.objects.filter(name_fa="").count(),
        media_count=MediaAsset.objects.count(),
        collection_count=Collection.objects.count(),
        seo_count=SeoPage.objects.count(),
        import_jobs=CatalogImportJob.objects.all()[:8],
    ))


@owner_required
def product_content(request, product_id=None):
    products = Product.objects.select_related("category").order_by("name", "id")
    product = get_object_or_404(Product, pk=product_id) if product_id else None
    form = ProductContentForm(request.POST or None, instance=product) if product else None
    if product and request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Bilingual product content saved.")
        return redirect("contentstudio:owner-product-content-edit", product_id=product.id)
    return render(request, "owner/content_products.html", _owner_context(request, products=products, product=product, form=form))


@owner_required
def category_content(request, category_id=None):
    categories = Category.objects.order_by("sort_order", "name")
    category = get_object_or_404(Category, pk=category_id) if category_id else None
    form = CategoryContentForm(request.POST or None, instance=category) if category else None
    if category and request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Bilingual category content saved.")
        return redirect("contentstudio:owner-category-content-edit", category_id=category.id)
    return render(request, "owner/content_categories.html", _owner_context(request, categories=categories, category=category, form=form))


@owner_required
def collections_manager(request, collection_id=None):
    instance = get_object_or_404(Collection, pk=collection_id) if collection_id else None
    form = CollectionForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        messages.success(request, "Collection saved.")
        return redirect("contentstudio:owner-collection-edit", collection_id=obj.id)
    collections = Collection.objects.select_related("hero").annotate(product_count=Count("items"))
    return render(request, "owner/content_collections.html", _owner_context(request, collections=collections, form=form, editing=instance, all_products=Product.objects.filter(is_active=True).order_by("name", "id") if instance else Product.objects.none()))


@require_POST
@owner_required
def collection_products(request, collection_id):
    collection = get_object_or_404(Collection, pk=collection_id)
    product_ids = [int(value) for value in request.POST.getlist("products") if value.isdigit()]
    with_selected = Product.objects.filter(pk__in=product_ids, is_active=True).order_by("id")
    CollectionItem.objects.filter(collection=collection).exclude(product_id__in=product_ids).delete()
    existing = set(CollectionItem.objects.filter(collection=collection, product_id__in=product_ids).values_list("product_id", flat=True))
    for index, product in enumerate(with_selected):
        if product.id in existing:
            CollectionItem.objects.filter(collection=collection, product=product).update(sort_order=index * 10)
        else:
            CollectionItem.objects.create(collection=collection, product=product, sort_order=index * 10)
    messages.success(request, "Collection products updated.")
    return redirect("contentstudio:owner-collection-edit", collection_id=collection.id)


@owner_required
def media_library(request):
    form = MediaAssetForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.uploaded_by = request.user
        item.save()
        messages.success(request, "Media uploaded.")
        return redirect("contentstudio:owner-media")
    return render(request, "owner/content_media.html", _owner_context(request, form=form, assets=MediaAsset.objects.all()[:120]))


@require_POST
@owner_required
def media_delete(request, asset_id):
    asset = get_object_or_404(MediaAsset, pk=asset_id)
    if asset.hero_collections.exists():
        messages.error(request, "This file is used as a collection hero. Remove it from the collection first.")
    else:
        asset.file.delete(save=False)
        asset.delete()
        messages.success(request, "Media deleted.")
    return redirect("contentstudio:owner-media")


@owner_required
def seo_manager(request, seo_id=None):
    instance = get_object_or_404(SeoPage, pk=seo_id) if seo_id else None
    form = SeoPageForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        item = form.save()
        messages.success(request, "SEO route saved.")
        return redirect("contentstudio:owner-seo-edit", seo_id=item.id)
    return render(request, "owner/content_seo.html", _owner_context(request, form=form, editing=instance, pages=SeoPage.objects.all()))


@owner_required
def bulk_catalog(request):
    form = BulkCatalogForm(request.POST or None, request.FILES or None)
    result = None
    if request.method == "POST" and form.is_valid():
        uploaded = form.cleaned_data["file"]
        mode = form.cleaned_data["mode"]
        try:
            result = import_catalog_csv(uploaded, actor=request.user, apply=mode == "apply")
        except (UnicodeDecodeError, ValidationError) as exc:
            messages.error(request, "; ".join(getattr(exc, "messages", [str(exc)])))
        else:
            status = CatalogImportJob.Status.IMPORTED if result["applied"] else (CatalogImportJob.Status.FAILED if result["errors"] else CatalogImportJob.Status.VALIDATED)
            CatalogImportJob.objects.create(
                file_name=uploaded.name,
                status=status,
                total_rows=result["total"],
                successful_rows=result["success"],
                errors=result["errors"],
                created_by=request.user,
            )
            if result["applied"]:
                messages.success(request, f"Imported {result['success']} catalog rows.")
            elif not result["errors"]:
                messages.success(request, f"Validation passed for {result['success']} rows. Re-upload with Apply import when ready.")
    return render(request, "owner/content_bulk.html", _owner_context(request, form=form, result=result, fields=CSV_FIELDS, jobs=CatalogImportJob.objects.all()[:20]))


@owner_required
def export_catalog(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="avan-catalog.csv"'
    response.write("\ufeff")
    writer = csv.DictWriter(response, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for row in catalog_csv_rows():
        writer.writerow(row)
    return response
