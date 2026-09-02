from .seo import rich_meta_for_request


def growth_meta(request):
    try:
        return {"AVAN_GROWTH_META": rich_meta_for_request(request)}
    except Exception:
        return {"AVAN_GROWTH_META": {}}
