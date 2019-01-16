from django import forms

from user.models import Invoice


class BuyForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    invoice = forms.ModelChoiceField(queryset=Invoice.objects.all())
