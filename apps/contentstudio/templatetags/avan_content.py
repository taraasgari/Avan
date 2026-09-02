import json

from django import template
from django.db import OperationalError, ProgrammingError
from django.utils import translation

from apps.contentstudio.models import SeoPage

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
    default = {
        "title": "AVAN",
        "description": "AVAN — fashion, design and drops",
        "canonical": request.build_absolute_uri(request.path),
        "noindex": False,
        "json_ld_json": "",
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
        "canonical": request.build_absolute_uri(page.canonical_path or page.path),
        "noindex": page.noindex,
        "json_ld_json": json.dumps(page.json_ld, ensure_ascii=False, separators=(",", ":")) if page.json_ld else "",
    })
    return payload
