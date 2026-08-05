"""Formulários de troca/devolução."""

from __future__ import annotations

from django import forms

from apps.orders.models import ReturnRequest


class ReturnRequestForm(forms.Form):
    order_number = forms.CharField(
        label="Número do pedido",
        max_length=32,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "TP-…"}),
    )
    email = forms.EmailField(
        label="E-mail da compra",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    kind = forms.ChoiceField(
        label="Tipo",
        choices=ReturnRequest.Kind.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    reason = forms.ChoiceField(
        label="Motivo",
        choices=ReturnRequest.Reason.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    details = forms.CharField(
        label="Detalhes",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )


class ReturnProcessForm(forms.Form):
    approve = forms.BooleanField(required=False, initial=True, label="Aprovar")
    staff_notes = forms.CharField(
        label="Notas internas",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )
