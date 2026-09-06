from django.urls import path

from .views import (
    DesignAIAPIView, DesignAssetUploadAPIView, DesignDetailAPIView, DesignLikeAPIView,
    DesignListCreateAPIView, DesignPublishAPIView, DesignRemixAPIView, DesignSaveAPIView,
    DesignStickerizeAPIView, PublicDesignDetailAPIView, PublicDesignListAPIView,
)

urlpatterns = [
    path("", DesignListCreateAPIView.as_view(), name="design-list-create"),
    path("assets/", DesignAssetUploadAPIView.as_view(), name="design-asset-upload"),
    path("ai/generate/", DesignAIAPIView.as_view(), name="design-ai-generate"),
    path("assets/<uuid:asset_id>/stickerize/", DesignStickerizeAPIView.as_view(), name="design-stickerize"),
    path("explore/", PublicDesignListAPIView.as_view(), name="design-explore-api"),
    path("explore/<uuid:design_id>/", PublicDesignDetailAPIView.as_view(), name="design-public-detail-api"),
    path("<uuid:design_id>/", DesignDetailAPIView.as_view(), name="design-detail"),
    path("<uuid:design_id>/publish/", DesignPublishAPIView.as_view(), name="design-publish"),
    path("<uuid:design_id>/remix/", DesignRemixAPIView.as_view(), name="design-remix"),
    path("<uuid:design_id>/like/", DesignLikeAPIView.as_view(), name="design-like"),
    path("<uuid:design_id>/save/", DesignSaveAPIView.as_view(), name="design-save"),
]
