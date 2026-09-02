from django import forms

from .models import SizePassport


class SizePassportForm(forms.ModelForm):
    class Meta:
        model = SizePassport
        fields = [
            "height_cm",
            "weight_kg",
            "chest_cm",
            "waist_cm",
            "hip_cm",
            "preferred_fit",
            "usual_top_size",
            "notes",
        ]
        widgets = {
            "height_cm": forms.NumberInput(attrs={"min": 120, "max": 230}),
            "weight_kg": forms.NumberInput(attrs={"min": 30, "max": 250}),
            "chest_cm": forms.NumberInput(attrs={"min": 50, "max": 180}),
            "waist_cm": forms.NumberInput(attrs={"min": 45, "max": 180}),
            "hip_cm": forms.NumberInput(attrs={"min": 50, "max": 200}),
            "notes": forms.TextInput(attrs={"maxlength": 240}),
        }
