"""Formulários da fila de revisão de manuais."""

from django import forms


class ManualUploadForm(forms.Form):
    file = forms.FileField(
        label="Manual PDF",
        help_text="Apenas PDF. Máx. conforme MANUAL_MAX_UPLOAD_BYTES.",
    )
    manufacturer = forms.CharField(
        label="Fabricante",
        required=False,
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ex.: Mondial"}),
    )


class ExtractionReviewForm(forms.Form):
    notes = forms.CharField(
        label="Notas da revisão",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
    corrected_json = forms.CharField(
        label="JSON corrigido (opcional)",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control font-monospace", "rows": 16}),
        help_text="Se preenchido, substitui o JSON da IA antes de gravar o rascunho.",
    )
