from django import forms
from apps.core.formmixins import BootstrapFormMixin
from .models import Supplier


class SupplierForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "phone", "email", "address"]
