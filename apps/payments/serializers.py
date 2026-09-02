from rest_framework import serializers
from .models import PaymentAttempt


class PaymentAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentAttempt
        fields = ["id", "provider", "amount", "status", "external_reference", "redirect_url", "created_at"]
