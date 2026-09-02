from django.utils import translation

from .ui import normalize_language


class AvanLocaleMiddleware:
    """Cookie-based UI locale. Product/user content is never auto-translated."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = normalize_language(request.COOKIES.get("avan_language") or "en")
        request.avan_language = language
        request.avan_dir = "rtl" if language == "fa" else "ltr"
        translation.activate("fa" if language == "fa" else "en")
        try:
            return self.get_response(request)
        finally:
            translation.deactivate()
