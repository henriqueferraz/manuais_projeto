from django import forms

from apps.tickets.models import Ticket


class TicketCreateForm(forms.Form):
    email = forms.EmailField(label="E-mail")
    title = forms.CharField(label="Assunto", max_length=200)
    equipment = forms.CharField(label="Equipamento / modelo", max_length=120, required=False)
    description = forms.CharField(label="Descrição", widget=forms.Textarea)
    priority = forms.ChoiceField(choices=Ticket.Priority.choices, initial=Ticket.Priority.MEDIUM)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = "form-select" if name == "priority" else "form-control"
            field.widget.attrs.setdefault("class", css)
        self.fields["description"].widget.attrs["rows"] = 4


class TicketStatusForm(forms.Form):
    status = forms.ChoiceField(choices=Ticket.Status.choices)
    note = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 2, "class": "form-control"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].widget.attrs["class"] = "form-select"
