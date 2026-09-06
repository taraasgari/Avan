from django import template
from django.conf import settings

from apps.core.ui import normalize_language, translate

register = template.Library()


def _language(context):
    request = context.get("request")
    if request is not None:
        request_language = getattr(request, "avan_language", None)
        if request_language:
            return normalize_language(request_language)
        cookie = request.COOKIES.get("avan_language")
        if cookie:
            return normalize_language(cookie)
    return "fa"


@register.simple_tag(takes_context=True)
def avan_t(context, key):
    return translate(key, _language(context))


@register.simple_tag(takes_context=True)
def avan_lang(context):
    return _language(context)


@register.simple_tag(takes_context=True)
def avan_dir(context):
    return "rtl" if _language(context) == "fa" else "ltr"
