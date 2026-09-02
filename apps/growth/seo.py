import json
import re
from urllib.parse import urlencode

from django.conf import settings


PRODUCT_RE = re.compile(r"^/shop/(?P<slug>[-a-zA-Z0-9_]+)/?$")
COLLECTION_RE = re.compile(r"^/collections/(?P<slug>[-a-zA-Z0-9_]+)/?$")
DESIGN_RE = re.compile(r"^/explore/(?P<id>[0-9a-fA-F-]+)/?$")
CREATOR_RE = re.compile(r"^/creator/(?P<username>[^/]+)/?$")


def _lang(request):
    value = getattr(request, "avan_language", None) or request.GET.get("lang") or "en"
    return "fa" if str(value).lower().startswith("fa") else "en"


def _absolute(request, path, **query):
    url = request.build_absolute_uri(path)
    if query:
        url += "?" + urlencode(query)
    return url


def _safe_image(request, image_field):
    try:
        return request.build_absolute_uri(image_field.url)
    except Exception:
        return ""


def _product_payload(request, product, language):
    name = product.localized_name(language)
    description = product.localized_seo_description(language)[:300]
    images = [_safe_image(request, item.image) for item in product.images.all()[:8]]
    images = [item for item in images if item]
    variants = list(product.variants.filter(is_active=True).select_related("color", "size"))
    prices_toman = [int(v.price) for v in variants] or [int(product.base_price)]
    # Schema.org uses ISO currency. Site prices are Toman, so IRR values are x10.
    low_irr = min(prices_toman) * 10
    high_irr = max(prices_toman) * 10
    any_stock = any(getattr(v, "available_stock", 0) > 0 for v in variants)
    canonical = _absolute(request, request.path, lang=language)
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": name,
        "description": description,
        "url": canonical,
        "brand": {"@type": "Brand", "name": "AVAN"},
        "image": images,
        "offers": {
            "@type": "AggregateOffer",
            "priceCurrency": "IRR",
            "lowPrice": low_irr,
            "highPrice": high_irr,
            "offerCount": max(1, len(variants)),
            "availability": "https://schema.org/InStock" if any_stock else "https://schema.org/OutOfStock",
            "url": canonical,
        },
    }
    if variants:
        schema["sku"] = variants[0].sku
    return {
        "title": product.localized_seo_title(language),
        "description": description,
        "og_type": "product",
        "og_image": images[0] if images else "",
        "schemas": [schema],
    }


def rich_meta_for_request(request):
    language = _lang(request)
    path = request.path
    result = {
        "language": language,
        "canonical": _absolute(request, path, lang=language),
        "alternate_en": _absolute(request, path, lang="en"),
        "alternate_fa": _absolute(request, path, lang="fa"),
        "og_type": "website",
        "og_image": "",
        "schemas": [],
    }

    organization = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "AVAN",
        "url": _absolute(request, "/"),
    }
    website = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "AVAN",
        "url": _absolute(request, "/"),
        "potentialAction": {
            "@type": "SearchAction",
            "target": _absolute(request, "/search/") + "?q={search_term_string}",
            "query-input": "required name=search_term_string",
        },
    }
    result["schemas"].extend([organization, website])

    match = PRODUCT_RE.match(path)
    if match:
        try:
            from apps.catalog.models import Product
            product = Product.objects.filter(slug=match.group("slug"), is_active=True).prefetch_related("images", "variants__color", "variants__size").first()
        except Exception:
            product = None
        if product:
            result.update(_product_payload(request, product, language))
            breadcrumb = {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "AVAN", "item": _absolute(request, "/")},
                    {"@type": "ListItem", "position": 2, "name": "Shop", "item": _absolute(request, "/shop/")},
                    {"@type": "ListItem", "position": 3, "name": product.localized_name(language), "item": result["canonical"]},
                ],
            }
            result["schemas"].append(breadcrumb)

    match = COLLECTION_RE.match(path)
    if match:
        try:
            from apps.contentstudio.models import Collection
            collection = Collection.objects.select_related("hero").filter(slug=match.group("slug"), is_active=True).first()
        except Exception:
            collection = None
        if collection:
            result["title"] = collection.localized_name(language)
            result["description"] = collection.localized_description(language)[:300]
            if collection.hero_id:
                result["og_image"] = _safe_image(request, collection.hero.file)
            result["schemas"].append({
                "@context": "https://schema.org",
                "@type": "CollectionPage",
                "name": result["title"],
                "description": result["description"],
                "url": result["canonical"],
            })

    match = DESIGN_RE.match(path)
    if match:
        try:
            from apps.designs.models import Design
            design = Design.objects.select_related("owner", "base_product").filter(
                id=match.group("id"), status="published", visibility="public"
            ).first()
        except Exception:
            design = None
        if design:
            result["title"] = f"{design.title} — AVAN"
            result["description"] = f"Design by {design.owner.display_name or design.owner.username} on AVAN."
            first = design.base_product.images.first()
            if first:
                result["og_image"] = _safe_image(request, first.image)
            result["schemas"].append({
                "@context": "https://schema.org",
                "@type": "CreativeWork",
                "name": design.title,
                "creator": {"@type": "Person", "name": design.owner.display_name or design.owner.username},
                "url": result["canonical"],
            })

    match = CREATOR_RE.match(path)
    if match:
        try:
            from django.contrib.auth import get_user_model
            creator = get_user_model().objects.filter(username__iexact=match.group("username"), public_profile_enabled=True).first()
        except Exception:
            creator = None
        if creator:
            display = creator.display_name or creator.username
            result["title"] = f"{display} — AVAN Creator"
            result["description"] = (creator.bio or f"Explore {display}'s public designs on AVAN.")[:300]
            if creator.avatar:
                result["og_image"] = _safe_image(request, creator.avatar)
            result["schemas"].append({
                "@context": "https://schema.org",
                "@type": "ProfilePage",
                "mainEntity": {"@type": "Person", "name": display},
                "url": result["canonical"],
            })

    result["schemas_json"] = [json.dumps(item, ensure_ascii=False, separators=(",", ":")) for item in result["schemas"]]
    return result
