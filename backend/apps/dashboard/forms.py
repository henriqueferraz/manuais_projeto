"""Forms do dashboard (hero da home)."""

from __future__ import annotations

from django import forms

from apps.dashboard.models import HomeHeroSlide


class HomeHeroSlideForm(forms.ModelForm):
    class Meta:
        model = HomeHeroSlide
        fields = (
            "badge",
            "title",
            "lead",
            "image",
            "alt_text",
            "sort_order",
            "is_active",
        )
        widgets = {
            "badge": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "TECNOLOGIA AI"}
            ),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "lead": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "alt_text": forms.TextInput(attrs={"class": "form-control"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
