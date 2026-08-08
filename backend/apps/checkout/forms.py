"""Forms do checkout."""

from django import forms


class CheckoutAddressForm(forms.Form):
    email = forms.EmailField(label="E-mail")
    shipping_name = forms.CharField(label="Nome completo", max_length=180)
    shipping_phone = forms.CharField(label="Telefone", max_length=32, required=False)
    shipping_cep = forms.CharField(label="CEP", max_length=9)
    shipping_street = forms.CharField(label="Rua", max_length=180)
    shipping_number = forms.CharField(label="Número", max_length=32)
    shipping_complement = forms.CharField(label="Complemento", max_length=120, required=False)
    shipping_district = forms.CharField(label="Bairro", max_length=120)
    shipping_city = forms.CharField(label="Cidade", max_length=120)
    shipping_state = forms.CharField(label="UF", max_length=2)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["shipping_cep"].widget.attrs["inputmode"] = "numeric"
        self.fields["shipping_phone"].widget.attrs["inputmode"] = "tel"
        self.fields["email"].widget.attrs["inputmode"] = "email"
        self.fields["shipping_state"].widget.attrs["maxlength"] = "2"
        self.fields["shipping_state"].widget.attrs["class"] += " tp-input-uf"


class CheckoutShippingForm(forms.Form):
    shipping_option_id = forms.CharField(widget=forms.HiddenInput)


class CheckoutPaymentForm(forms.Form):
    """
    Token do gateway (Stripe PM / MP card token / mock tok_xxx).
    Nunca envie número de cartão a este form em produção.
    """

    payment_token = forms.CharField(
        label="Token de pagamento",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-control font-monospace",
                "placeholder": "tok_sandbox_4242",
                "autocomplete": "off",
            }
        ),
        help_text="Em produção o token vem do SDK do gateway no browser.",
    )
