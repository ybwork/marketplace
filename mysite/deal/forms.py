from django import forms

from user.models import Invoice


class DealPayForm(forms.Form):
    amount = forms.DecimalField(min_value=1, max_digits=10, decimal_places=2)
    invoice = forms.ModelChoiceField(queryset=Invoice.objects.all())
