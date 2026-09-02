from django import forms

from .models import Address, ProductionBatch, ReturnRequest, Shipment, Supplier


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["title", "recipient_name", "phone", "province", "city", "address", "postal_code", "is_default"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}


class ReturnRequestForm(forms.ModelForm):
    class Meta:
        model = ReturnRequest
        fields = ["reason", "customer_note"]
        widgets = {"customer_note": forms.Textarea(attrs={"rows": 4})}


class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ["method", "status", "carrier_name", "tracking_code", "owner_note"]
        widgets = {"owner_note": forms.Textarea(attrs={"rows": 3})}


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "contact_name", "phone", "email", "notes", "is_active"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class ProductionBatchForm(forms.ModelForm):
    class Meta:
        model = ProductionBatch
        fields = ["reference", "product", "supplier", "status", "planned_quantity", "completed_quantity", "expected_at", "notes"]
        widgets = {"expected_at": forms.DateInput(attrs={"type": "date"}), "notes": forms.Textarea(attrs={"rows": 3})}
