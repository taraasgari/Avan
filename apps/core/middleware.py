from django.utils import translation

from .ui import normalize_language


class AvanLocaleMiddleware:
    """Stable bilingual UI locale.

    ?lang=en / ?lang=fa are crawlable, deterministic language variants for SEO.
    The selected language is also persisted in a cookie for normal navigation.
    User/product content is never machine-translated.
    """

    COOKIE_NAME = "avan_language"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        requested = request.GET.get("lang")
        language = normalize_language(requested or request.COOKIES.get(self.COOKIE_NAME) or "en")
        request.avan_language = language
        request.avan_dir = "rtl" if language == "fa" else "ltr"
        translation.activate("fa" if language == "fa" else "en")
        try:
            response = self.get_response(request)
            if requested is not None:
                response.set_cookie(
                    self.COOKIE_NAME,
                    language,
                    max_age=365 * 24 * 60 * 60,
                    samesite="Lax",
                    secure=request.is_secure(),
                    httponly=False,
                )
            response.headers.setdefault("Content-Language", language)
            response.headers.setdefault("Vary", "Cookie")
            return response
        finally:
            translation.deactivate()
