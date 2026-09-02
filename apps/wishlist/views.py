from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Product
from .models import WishlistItem
from .serializers import WishlistItemSerializer


class WishlistAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = WishlistItem.objects.filter(user=request.user).select_related("product")
        return Response(WishlistItemSerializer(qs, many=True).data)

    def post(self, request):
        product = get_object_or_404(Product, pk=request.data.get("product_id"), is_active=True)
        item, _ = WishlistItem.objects.get_or_create(user=request.user, product=product)
        return Response(WishlistItemSerializer(item).data, status=201)


class WishlistItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        WishlistItem.objects.filter(user=request.user, product_id=product_id).delete()
        return Response(status=204)
