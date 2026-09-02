from rest_framework import serializers

from .models import Order, OrderItem, StockReservation


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "product_name",
            "sku",
            "color_name",
            "size_name",
            "unit_price",
            "quantity",
            "line_total",
            "is_customized",
            "design_id_snapshot",
            "design_title",
            "design_owner_name",
            "design_snapshot",
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    reservation_expires_at = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()
    shipping = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "number",
            "status",
            "subtotal",
            "discount_amount",
            "shipping_amount",
            "total_amount",
            "customer_name",
            "phone",
            "email",
            "province",
            "city",
            "address",
            "postal_code",
            "customer_note",
            "paid_at",
            "created_at",
            "items",
            "reservation_expires_at",
            "payment",
            "shipping",
        ]

    def get_reservation_expires_at(self, obj):
        reservation = obj.reservations.filter(status=StockReservation.Status.ACTIVE).order_by("expires_at").first()
        return reservation.expires_at if reservation else None

    def get_payment(self, obj):
        payment = obj.payment_attempts.order_by("-created_at").first()
        if not payment:
            return None
        return {
            "id": str(payment.id),
            "provider": payment.provider,
            "status": payment.status,
            "amount": payment.amount,
            "redirect_url": payment.redirect_url,
        }

    def get_shipping(self, obj):
        try:
            shipment = obj.shipment
        except Exception:
            return None
        if not shipment:
            return None
        method = shipment.method
        return {
            "status": shipment.status,
            "tracking_code": shipment.tracking_code,
            "carrier_name": shipment.carrier_name,
            "method_id": method.id if method else None,
            "method_code": method.code if method else None,
            "method_name_en": method.name_en if method else None,
            "method_name_fa": method.name_fa if method else None,
        }


class CheckoutSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(required=False)
    shipping_method_id = serializers.IntegerField(required=False)
    customer_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    province = serializers.CharField(max_length=80, required=False, allow_blank=True)
    city = serializers.CharField(max_length=80, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=30, required=False, allow_blank=True)
    customer_note = serializers.CharField(required=False, allow_blank=True)
    idempotency_key = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if not attrs.get("address_id"):
            required = ["customer_name", "phone", "province", "city", "address"]
            missing = [name for name in required if not str(attrs.get(name, "")).strip()]
            if missing:
                raise serializers.ValidationError({name: "This field is required." for name in missing})
        return attrs
