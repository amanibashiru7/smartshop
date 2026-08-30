from django import forms
from apps.core.formmixins import BootstrapFormMixin
from .models import Customer


class CustomerForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone", "email", "address"]


class PaymentForm(BootstrapFormMixin, forms.Form):
    amount = forms.DecimalField(min_value=0.01, max_digits=12, decimal_places=2)
    note = forms.CharField(max_length=255, required=False)
