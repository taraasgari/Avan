import json

from django import template
from django.db import OperationalError, ProgrammingError
from django.utils import translation

from apps.contentstudio.models import SeoPage
from apps.growth.seo import rich_meta_for_request

register = template.Library()


def _lang(request=None):
    if request is not None:
        value = getattr(request, "avan_language", None) or getattr(request, "LANGUAGE_CODE", None)
        if value:
            return "fa" if str(value).lower().startswith("fa") else "en"
    value = translation.get_language() or "en"
    return "fa" if str(value).lower().startswith("fa") else "en"


@register.simple_tag
def product_name(product, request=None):
    return product.localized_name(_lang(request))


@register.simple_tag
def product_description(product, request=None):
    return product.localized_description(_lang(request))


@register.simple_tag
def category_name(category, request=None):
    return category.localized_name(_lang(request))


@register.simple_tag
def seo_for_request(request):
    language = _lang(request)
    dynamic = rich_meta_for_request(request)
    default = {
        "title": dynamic.get("title") or "AVAN",
        "description": dynamic.get("description") or "AVAN — fashion, design and drops",
        "canonical": dynamic.get("canonical") or request.build_absolute_uri(request.path),
        "alternate_en": dynamic.get("alternate_en") or request.build_absolute_uri(request.path + "?lang=en"),
        "alternate_fa": dynamic.get("alternate_fa") or request.build_absolute_uri(request.path + "?lang=fa"),
        "noindex": False,
        "json_ld_json": "",
        "schemas_json": dynamic.get("schemas_json", []),
        "og_type": dynamic.get("og_type", "website"),
        "og_image": dynamic.get("og_image", ""),
    }
    try:
        page = SeoPage.objects.filter(path=request.path).first()
    except (OperationalError, ProgrammingError):
        page = None
    if not page:
        return default
    payload = dict(default)
    payload.update({
        "title": page.localized_title(language) or default["title"],
        "description": page.localized_description(language) or default["description"],
        "canonical": request.build_absolute_uri(page.canonical_path or request.path) + ("?lang=" + language),
        "noindex": page.noindex,
        "json_ld_json": json.dumps(page.json_ld, ensure_ascii=False, separators=(",", ":")) if page.json_ld else "",
    })
    return payload
