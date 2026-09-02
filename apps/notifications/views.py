from rest_framework import generics, permissions
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
