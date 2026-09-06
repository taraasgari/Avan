from copy import deepcopy
from decimal import Decimal, InvalidOperation

from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification
from apps.marketplace.models import MarketplaceSettings
from apps.growth.security import validate_uploaded_image
from .ai import generate_ai_design, stickerize_asset
from .models import Design, DesignAsset, DesignLike, DesignSave, StudioSettings
from .serializers import DesignAssetSerializer, DesignSerializer


def public_designs():
    return (
        Design.objects
        .filter(status=Design.Status.PUBLISHED, visibility=Design.Visibility.PUBLIC)
        .select_related("owner", "base_product", "base_color")
        .prefetch_related("remixes", "likes", "saves")
    )


def notify_social(*, user, title, body, url):
    if not user:
        return
    Notification.objects.create(user=user, kind=Notification.Kind.SOCIAL, title=title, body=body, url=url)


class DesignListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        qs = Design.objects.filter(owner=request.user).select_related("base_product", "base_color", "owner").prefetch_related("remixes", "likes", "saves")
        return Response(DesignSerializer(qs, many=True, context={"request": request}).data)
    def post(self, request):
        serializer = DesignSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        design = serializer.save(owner=request.user)
        return Response(DesignSerializer(design, context={"request": request}).data, status=status.HTTP_201_CREATED)


class DesignDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get_object(self, request, design_id):
        return get_object_or_404(Design.objects.select_related("base_product", "base_color", "owner").prefetch_related("remixes", "likes", "saves"), id=design_id, owner=request.user)
    def get(self, request, design_id):
        return Response(DesignSerializer(self.get_object(request, design_id), context={"request": request}).data)
    def patch(self, request, design_id):
        design = self.get_object(request, design_id)
        serializer = DesignSerializer(design, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(DesignSerializer(design, context={"request": request}).data)
    def delete(self, request, design_id):
        self.get_object(request, design_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DesignPublishAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, design_id):
        design = get_object_or_404(Design, id=design_id, owner=request.user)
        design.status = Design.Status.PUBLISHED
        design.visibility = Design.Visibility.PUBLIC
        design.allow_remix = bool(request.data.get("allow_remix", design.allow_remix))
        design.is_for_sale = bool(request.data.get("is_for_sale", design.is_for_sale))
        config = MarketplaceSettings.load()
        if config.creator_pricing_enabled:
            raw_sale_price = request.data.get("sale_price", design.sale_price)
            try:
                sale_price = Decimal(str(raw_sale_price or 0))
            except (InvalidOperation, TypeError, ValueError):
                return Response({"detail": "Invalid creator design fee."}, status=400)
            if sale_price < 0 or sale_price != sale_price.quantize(Decimal("1")):
                return Response({"detail": "Creator design fee must be a non-negative whole Toman amount."}, status=400)
            design.sale_price = sale_price
        else:
            design.sale_price = Decimal("0")
        if not design.published_at:
            design.published_at = timezone.now()
        design.save(update_fields=["status", "visibility", "allow_remix", "is_for_sale", "sale_price", "published_at", "updated_at"])
        return Response(DesignSerializer(design, context={"request": request}).data)


class PublicDesignListAPIView(APIView):
    def get(self, request):
        sort = request.GET.get("sort", "newest")
        qs = public_designs().annotate(likes_total=Count("likes", distinct=True), remixes_total=Count("remixes", distinct=True))
        qs = qs.order_by("-likes_total", "-remixes_total", "-published_at") if sort == "popular" else qs.order_by("-published_at")
        return Response(DesignSerializer(qs[:48], many=True, context={"request": request}).data)


class PublicDesignDetailAPIView(APIView):
    def get(self, request, design_id):
        return Response(DesignSerializer(get_object_or_404(public_designs(), id=design_id), context={"request": request}).data)


class DesignRemixAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, design_id):
        source = get_object_or_404(Design.objects.select_related("base_product", "base_color", "owner"), id=design_id)
        allowed = source.owner_id == request.user.id or (source.status == Design.Status.PUBLISHED and source.visibility == Design.Visibility.PUBLIC and source.allow_remix)
        if not allowed:
            return Response({"detail": "This design is not available for remix."}, status=403)
        remix = Design.objects.create(owner=request.user, base_product=source.base_product, base_color=source.base_color, title=f"Remix of {source.title}"[:120], parent_design=source, design_data=deepcopy(source.design_data))
        if source.owner_id != request.user.id:
            notify_social(user=source.owner, title="Your design was remixed", body=f"{request.user.display_name or request.user.username} remixed {source.title}.", url=f"/explore/{source.id}/")
        return Response(DesignSerializer(remix, context={"request": request}).data, status=status.HTTP_201_CREATED)


class DesignLikeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, design_id):
        design = get_object_or_404(public_designs(), id=design_id)
        like, created = DesignLike.objects.get_or_create(user=request.user, design=design)
        if not created:
            like.delete()
        elif design.owner_id != request.user.id:
            notify_social(user=design.owner, title="New design like", body=f"{request.user.display_name or request.user.username} liked {design.title}.", url=f"/explore/{design.id}/")
        return Response({"active": created, "count": design.likes.count()})


class DesignSaveAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, design_id):
        design = get_object_or_404(public_designs(), id=design_id)
        saved, created = DesignSave.objects.get_or_create(user=request.user, design=design)
        if not created:
            saved.delete()
        return Response({"active": created, "count": design.saves.count()})


class DesignAssetUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp"}
    def get(self, request):
        kind = request.GET.get("kind")
        qs = DesignAsset.objects.filter(owner=request.user)
        if kind in DesignAsset.Kind.values:
            qs = qs.filter(kind=kind)
        return Response(DesignAssetSerializer(qs[:80], many=True, context={"request": request}).data)
    def post(self, request):
        upload = request.FILES.get("image")
        if not upload:
            return Response({"detail": "Image is required."}, status=400)
        if upload.content_type not in self.ALLOWED_TYPES:
            return Response({"detail": "Use PNG, JPEG or WebP."}, status=400)
        config = StudioSettings.load()
        try:
            validate_uploaded_image(upload, max_bytes=config.max_upload_mb * 1024 * 1024, max_width=8000, max_height=8000)
        except Exception as exc:
            messages = getattr(exc, "messages", None)
            return Response({"detail": "; ".join(messages) if messages else "Invalid image upload."}, status=400)
        kind = request.data.get("kind", DesignAsset.Kind.IMAGE)
        if kind not in DesignAsset.Kind.values:
            kind = DesignAsset.Kind.IMAGE
        if kind == DesignAsset.Kind.STICKER and not config.allow_user_stickers:
            return Response({"detail": "Personal stickers are disabled."}, status=403)
        asset = DesignAsset.objects.create(owner=request.user, image=upload, original_name=upload.name[:255], mime_type=upload.content_type or "", kind=kind)
        return Response(DesignAssetSerializer(asset, context={"request": request}).data, status=status.HTTP_201_CREATED)


class DesignAIAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            asset = generate_ai_design(user=request.user, prompt=request.data.get("prompt", ""))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        except RuntimeError as exc:
            return Response({"detail": str(exc)}, status=503)
        return Response(DesignAssetSerializer(asset, context={"request": request}).data, status=201)


class DesignStickerizeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, asset_id):
        asset = get_object_or_404(DesignAsset, id=asset_id, owner=request.user)
        try:
            sticker = stickerize_asset(user=request.user, asset=asset)
        except Exception as exc:
            return Response({"detail": str(exc) or "Could not create sticker."}, status=400)
        return Response(DesignAssetSerializer(sticker, context={"request": request}).data, status=201)
